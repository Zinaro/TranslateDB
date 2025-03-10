#include <gtk/gtk.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <limits.h>
#include <string.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <glib.h>

GtkWidget *status_label;
GtkWidget *url_label;
GtkWidget *start_button;
GtkWidget *text_view;
GtkTextBuffer *text_buffer;
GtkWidget *scrolled_window;
GPid app_child_pid = 0;
GPid temp_pid = 0;

void stop_app(GtkWidget *widget, gpointer data);
void start_app(GtkWidget *widget, gpointer data);
void terminate_child();
void signal_handler(int signum);
void clean_up();
void apply_terminal_style(GtkWidget *widget);

void append_text(const char *text)
{
    GtkTextIter end;
    gtk_text_buffer_get_end_iter(text_buffer, &end);
    gtk_text_buffer_insert(text_buffer, &end, text, -1);
}

gboolean read_output(GIOChannel *source, GIOCondition condition, gpointer data)
{
    gchar buffer[256];
    gsize bytes_read;
    GError *error = NULL;

    if (g_io_channel_read_chars(source, buffer, sizeof(buffer) - 1, &bytes_read, &error) == G_IO_STATUS_NORMAL)
    {
        buffer[bytes_read] = '\0';
        append_text(buffer);
    }

    if (condition & (G_IO_HUP | G_IO_ERR))
    {
        g_io_channel_shutdown(source, TRUE, NULL);
        g_io_channel_unref(source);
        return FALSE;
    }

    return TRUE;
}

void on_child_exit(GPid pid, gint status, gpointer data)
{
    g_spawn_close_pid(pid);
    if (pid == app_child_pid)
    {
        app_child_pid = 0;
        append_text("The app.py process has terminated.\n");
    }
}

void run_app_command_async(char *const argv[], GPid *pid)
{
    gint stdout_fd, stderr_fd;
    GIOChannel *stdout_channel, *stderr_channel;
    GError *error = NULL;

    if (!g_spawn_async_with_pipes(NULL, (gchar **)argv, NULL, G_SPAWN_DO_NOT_REAP_CHILD, NULL, NULL, pid, NULL, &stdout_fd, &stderr_fd, &error))
    {
        append_text("Error: Process failed to start!\n");
        if (error != NULL)
        {
            append_text(error->message);
            g_error_free(error);
        }
        return;
    }

    stdout_channel = g_io_channel_unix_new(stdout_fd);
    stderr_channel = g_io_channel_unix_new(stderr_fd);

    g_io_channel_set_flags(stdout_channel, G_IO_FLAG_NONBLOCK, NULL);
    g_io_channel_set_flags(stderr_channel, G_IO_FLAG_NONBLOCK, NULL);

    g_io_add_watch(stdout_channel, G_IO_IN | G_IO_HUP | G_IO_ERR, (GIOFunc)read_output, NULL);
    g_io_add_watch(stderr_channel, G_IO_IN | G_IO_HUP | G_IO_ERR, (GIOFunc)read_output, NULL);

    g_child_watch_add(*pid, on_child_exit, NULL);
}

gboolean open_browser(gpointer data)
{
    g_spawn_command_line_async("xdg-open http://localhost:2000", NULL);
    return FALSE;
}

void start_app(GtkWidget *widget, gpointer data)
{
    if (app_child_pid != 0)
        return;
    gchar *python_path = g_find_program_in_path("python3");
    if (!python_path)
    {
        append_text("Error: python3 not found in PATH.\n");
        return;
    }

    char path[PATH_MAX], venv_dir[PATH_MAX], venv_python[PATH_MAX], venv_pip[PATH_MAX], app_py[PATH_MAX], req_file[PATH_MAX];
    if (readlink("/proc/self/exe", path, sizeof(path)) == -1)
    {
        append_text("Error: Unable to determine executable path.\n");
        g_free(python_path);
        return;
    }
    char *last_slash = strrchr(path, '/');
    if (!last_slash)
    {
        append_text("Error: Invalid executable path.\n");
        g_free(python_path);
        return;
    }
    *last_slash = '\0';
    snprintf(venv_dir, sizeof(venv_dir), "%s/venv", path);
    snprintf(venv_python, sizeof(venv_python), "%s/bin/python", venv_dir);
    snprintf(venv_pip, sizeof(venv_pip), "%s/bin/pip", venv_dir);
    snprintf(app_py, sizeof(app_py), "%s/app.py", path);
    snprintf(req_file, sizeof(req_file), "%s/requirements.txt", path);
    if (access(venv_python, F_OK) == -1)
    {
        append_text("Creating virtual environment...\n");
        GPid temp_pid;
        run_app_command_async((char *[]){python_path, "-m", "venv", venv_dir, NULL}, &temp_pid);
        append_text("The virtual environment was successfully created...\n");
    }
    else
    {
        if (access(req_file, F_OK) == -1)
        {
            append_text("Error: requirements.txt not found.\n");
            g_free(python_path);
            return;
        }
        FILE *req_file_ptr = fopen(req_file, "r");
        char package[256];
        gboolean dependencies_missing = FALSE;

        while (fgets(package, sizeof(package), req_file_ptr))
        {
            package[strcspn(package, "\n")] = 0;
            if (strlen(package) == 0)
                continue;
            char pkg_name[256];
            strncpy(pkg_name, package, sizeof(pkg_name));
            pkg_name[sizeof(pkg_name) - 1] = '\0';
            char *pos = strstr(pkg_name, "==");
            if (pos)
                *pos = '\0';
            int exit_status;
            gboolean success = g_spawn_sync(
                NULL,
                (char *[]){venv_pip, "show", pkg_name, NULL},
                NULL,
                G_SPAWN_DEFAULT,
                NULL,
                NULL,
                NULL,
                NULL,
                &exit_status,
                NULL);
            if (!success || exit_status != 0)
            {
                dependencies_missing = TRUE;
                break;
            }
        }
        fclose(req_file_ptr);
        if (dependencies_missing)
        {
            append_text("Installing dependencies...\n");
            run_app_command_async((char *[]){venv_pip, "install", "-r", req_file, NULL}, &app_child_pid);
            g_free(python_path);
            return;
        }
        else
        {
            if (access(app_py, F_OK) == -1)
            {
                append_text("Error: app.py not found.\n");
                g_free(python_path);
                return;
            }

            append_text("Starting app.py...\n");
            run_app_command_async((char *[]){venv_python, "app.py", NULL}, &app_child_pid);

            gtk_label_set_text(GTK_LABEL(status_label), "TranslateDB started!");
            gtk_label_set_markup(GTK_LABEL(url_label), "<span foreground='lightblue'>Running at: http://localhost:2000</span>");
            gtk_button_set_label(GTK_BUTTON(start_button), "Stop TranslateDB");

            g_signal_handlers_disconnect_by_func(start_button, G_CALLBACK(start_app), NULL);
            g_signal_connect(start_button, "clicked", G_CALLBACK(stop_app), NULL);
            g_timeout_add_seconds(2, open_browser, NULL);
        }
    }

    g_free(python_path);
}

void stop_app(GtkWidget *widget, gpointer data)
{
    terminate_child();
    gtk_label_set_text(GTK_LABEL(status_label), "TranslateDB stopped!");
    gtk_button_set_label(GTK_BUTTON(start_button), "Start TranslateDB");
    g_signal_handlers_disconnect_by_func(start_button, G_CALLBACK(stop_app), NULL);
    g_signal_connect(start_button, "clicked", G_CALLBACK(start_app), NULL);
}

void terminate_child()
{
    if (app_child_pid != 0)
    {
        if (kill(app_child_pid, SIGTERM) != 0)
        {
            kill(app_child_pid, SIGKILL);
        }
        waitpid(app_child_pid, NULL, 0);
        app_child_pid = 0;
        append_text("The server has been stopped.\n");
    }
}
void signal_handler(int signum)
{
    terminate_child();
    gtk_main_quit();
    exit(0);
}
void clean_up()
{
    terminate_child();
}
void apply_terminal_style(GtkWidget *widget)
{
    GtkCssProvider *provider = gtk_css_provider_new();
    gtk_css_provider_load_from_data(provider,
                                    "* {"
                                    "   background-color: black;"
                                    "   color: lightgreen;"
                                    "   font-family: 'Monospace';"
                                    "   font-size: 12px;"
                                    "}",
                                    -1, NULL);

    GtkStyleContext *context = gtk_widget_get_style_context(widget);
    gtk_style_context_add_provider(context, GTK_STYLE_PROVIDER(provider), GTK_STYLE_PROVIDER_PRIORITY_USER);
    g_object_unref(provider);
}

int main(int argc, char *argv[])
{
    gtk_init(&argc, &argv);

    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    signal(SIGQUIT, signal_handler);
    atexit(clean_up);

    GtkWidget *window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(window), "TranslateDB Launcher");
    gtk_window_set_default_size(GTK_WINDOW(window), 500, 400);

    GtkWidget *vbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 5);
    gtk_container_add(GTK_CONTAINER(window), vbox);

    start_button = gtk_button_new_with_label("Start TranslateDB");
    g_signal_connect(start_button, "clicked", G_CALLBACK(start_app), NULL);
    gtk_box_pack_start(GTK_BOX(vbox), start_button, FALSE, FALSE, 0);

    status_label = gtk_label_new("Ready");
    gtk_box_pack_start(GTK_BOX(vbox), status_label, FALSE, FALSE, 0);

    url_label = gtk_label_new("");
    gtk_box_pack_start(GTK_BOX(vbox), url_label, FALSE, FALSE, 0);

    scrolled_window = gtk_scrolled_window_new(NULL, NULL);
    gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scrolled_window), GTK_POLICY_AUTOMATIC, GTK_POLICY_AUTOMATIC);

    text_view = gtk_text_view_new();
    apply_terminal_style(text_view);
    text_buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(text_view));

    gtk_container_add(GTK_CONTAINER(scrolled_window), text_view);
    gtk_box_pack_start(GTK_BOX(vbox), scrolled_window, TRUE, TRUE, 0);

    g_signal_connect(window, "destroy", G_CALLBACK(clean_up), NULL);
    g_signal_connect(window, "destroy", G_CALLBACK(gtk_main_quit), NULL);

    gtk_widget_show_all(window);
    gtk_main();

    return 0;
}
