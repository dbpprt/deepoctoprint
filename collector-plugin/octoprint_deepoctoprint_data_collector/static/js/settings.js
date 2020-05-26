$(function() {
    function DeepOctoPrintDataCollectorViewModel(parameters) {
        var self = this;
        console.log("yldgf")
         self.settingsViewModel = parameters[0];
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: DeepOctoPrintDataCollectorViewModel,
        dependencies: ["settingsViewModel", "wizardViewModel"],
        elements: [ "#settings_plugin_deepoctoprint_data_collector",  "#wizard_plugin_deepoctoprint_data_collector"]
    });
});
