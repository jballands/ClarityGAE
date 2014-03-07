import "dart:html";

main() {
    //Load the console's configuration file asyncronously
    var configUrl = '/static/data/data-config.json';
    var configRequest = HttpRequest.getString(configUrl).then(onConfigLoad);
}

onConfigLoad(response) {
    window.alert(response);
}