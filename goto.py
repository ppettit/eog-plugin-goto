from gi.repository import Gio, GLib, GObject, Gtk, Eog


class Goto(GObject.Object, Eog.WindowActivatable):
    """Click on pic number in status bar to goto any pic in folder"""

    window = GObject.property(type=Eog.Window)
    label = None
    dialog = None

    def __init__(self):
        super(Goto, self).__init__()

    def do_activate(self):
        self.store = self.window.get_store()
        self.status_bar = self.window.get_statusbar()
        Gtk.Container.foreach(self.status_bar, self.find_img_num_label)
        Gtk.Container.remove(self.status_bar, self.label)
        self.menu_box = Gtk.MenuButton()
        self.menu_box.add(self.label)
        self.menu_box.show()
        menumodel = Gio.Menu()
        menumodel.append("Goto first", "win.go-first")
        menumodel.append("Goto last", "win.go-last")
        menumodel.append("Goto...", "win.goto")
        self.menu_box.set_menu_model(menumodel)
        self.status_bar.pack_end(self.menu_box, False, True, 6)

        action = Gio.SimpleAction.new('goto')
        action.connect('activate', self.on_goto)
        self.window.add_action(action)

        self.thumb_view = self.window.get_thumb_view()
        self.thumb_view.connect(
            'selection-changed',
            lambda widget:
            GLib.timeout_add(100, self.on_selection_changed, widget))

        self.current_image = self.window.lookup_action('current-image')

        self.setup_goto_widgets()

    def setup_goto_widgets(self):
        self.adjustment = Gtk.Adjustment(1, 1, 1, 1, 10, 0)
        self.adjustment.connect('value-changed', self.on_move)

        self.selection_scale = Gtk.Scale.new(
            Gtk.Orientation.HORIZONTAL, self.adjustment)
        self.selection_scale.set_round_digits(0)
        self.selection_scale.set_draw_value(False)
        self.selection_scale.connect('button-release-event', self.on_move)

        self.selection_spin = Gtk.SpinButton.new(self.adjustment, 1, 0)

    def do_deactivate(self):
        self.menu_box.remove(self.label)
        self.menu_box.destroy()
        self.status_bar.pack_end(self.label, False, True, 6)

    def on_goto(self, action, param):
        self.dialog = Gtk.Dialog()
        self.dialog.set_title("Goto...")
        self.dialog.set_transient_for(self.window)
        self.dialog.set_modal(False)

        content_area = self.dialog.get_content_area()
        vbox = Gtk.VBox()
        content_area.add(vbox)
        vbox.add(self.selection_scale)
        vbox.add(self.selection_spin)
        self.dialog.connect("response", self.on_response)
        self.dialog.set_default_size(
            self.window.get_allocated_width() * .75, -1)
        self.dialog.show_all()
        self.on_selection_changed()

    def on_response(self, dialog, response):
        if response == Gtk.ResponseType.DELETE_EVENT:
            self.setup_goto_widgets()
            self.on_selection_changed()

    def on_move(self, widget, param=None):
        pos = widget.get_value() - 1
        store = self.window.get_store()
        p = store.get_pos_by_image(self.window.get_image())
        if int(pos) is not p:
            image = store.get_image_by_pos(pos)
            self.thumb_view.set_current_image(image, True)
            self.on_selection_changed()

    def on_selection_changed(self, widget=None):
        state = self.current_image.get_state()
        store = self.window.get_store()
        upper = store.length()
        pos = store.get_pos_by_image(self.window.get_image()) + 1
        state = (pos, upper)
        if state[0] is not int(self.adjustment.get_value()):
            self.adjustment.set_value(state[0])
        if state[1] is not int(self.adjustment.get_upper()):
            self.adjustment.set_upper(state[1])

    def find_img_num_label(self, widget):
        if widget.get_name() == 'GtkLabel':
            self.label = widget
