import sublime
import sublime_plugin
import urllib
import json
import itertools


class TranslatePhraseCommand(sublime_plugin.TextCommand):

    """
    This command allows the selection of one of multiple translation pairs,
    shows an input panel for a phrase and then lets the user select one of the available results.
    """

    def __init__(self, *args, **kwargs):
        self.settings = sublime.load_settings(
            "TranslatePlugin.sublime-settings")
        # generate all possible translation pairs
        self.translations = list(
            itertools.permutations(self.settings.get("langs"), 2))
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)

    def run(self, edit):
        self.view.window().show_quick_panel(["{x[0][long]} -> {x[1][long]}".format(x=x) for x in self.translations], self.selected)

    def selected(self, x):
        """
        Callback when a translation pair was selected
        """
        if x != -1:
            self.trans = self.translations[x]
            self.view.window().show_input_panel(
                "Enter a word: ", "", self.text_input, None, None)

    def text_input(self, text):
        """
        Called once a phrase to translate was written
        """
        def no_result():
            self.view.window().status_message("Found no translations!")

        # Use the glosbe dictionary API for translations.
        url = "https://glosbe.com/gapi/translate?from={}&dest={}&format=json&phrase={}&pretty=false".format(
            self.trans[0]["short"], self.trans[1]["short"], urllib.parse.quote_plus(text))
        res = urllib.request.urlopen(url).readall().decode("utf-8")
        resDict = json.loads(res)

        # The resulting JSON from glosbe should have "result": "ok" and contain a list called "tuc".
        # tuc contains objects that are word definitions or translations (called "phrases")
        # We are only interested in the texts of phrases, could have used a
        # list comprehension instead
        if resDict['result'] == "ok":
            tuc = resDict["tuc"]
            phrases = [x["phrase"]["text"] for x in tuc if "phrase" in x]

            # If we get no phrases, show a status message
            if len(phrases) == 0:
                no_result()
            else:
                # Store the found phrases in this object and open a quick panel
                # for the user to choose a translation
                self.phrases_available = phrases
                self.view.window().show_quick_panel(
                    list(phrases), self.selected_trans)
        else:
            no_result()

    def selected_trans(self, x):
        """
        Callback function for when a translation was selected.
        """
        if x != -1:
            self.view.run_command("insert", {"characters": self.phrases_available[x]})
