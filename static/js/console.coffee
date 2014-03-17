root = this

#Console variables
root.dataConfig = {}

root.dataCurrentModel = ''
root.dataCurrentQuery = {}
root.dataCurrentOffset = 0
#END Console variables

initialize = ->
    #Disable any stragglers
    $('.load-disable').prop 'disabled', true
    (apiCall '/static/data/data-config.json', method = 'get').done (data) ->
        root.dataConfig = data
        do dataInitButtons

#Api call method for stadardizing api calls :D
apiCall = (url, data={}, method='post') ->
    #Disable elements that are marked to be
    $('.load-disable').prop 'disabled', true
    
    #Show that spiffy loader sprite
    do $('#loader').show
    
    #Start that AJAX up
    return $.ajax
        'url': url
        'method': method
        'contentType': 'application/json; charset=utf-8'
        'dataType': 'json'
        'data': JSON.stringify data
        'error': (xhr, status, error) ->
            bootbox.alert (xhr.responseText or error)
        'complete': ->
            do $('#loader').hide
            $('.load-disable').prop 'disabled', false

#Runs after the config file is loaded and deploys the selection buttons
dataInitButtons = ->
    do $('#data_buttonRow .btn').remove
    for model in root.dataConfig['models']
        modelName = root.dataConfig['names'][model]
        markup = "<label class='btn btn-primary load-disable'><input type='radio'>#{modelName}</label>"
        button = $(markup).appendTo $('#data_buttonRow')
        button.data 'model', model
        button.click ->
            dataLoadTable $(this).data('model')
    do $('#data_buttonRow .btn').button
    return

#Calls the api, and passes the data to the parser
dataLoadTable = (model = root.dataCurrentModel, query = root.dataCurrentQuery, offset = root.dataCurrentOffset) ->
    #Set it again, so the parser can see changes
    root.dataCurrentModel = model
    
    #Construct a url
    url = "/api/#{model}_query"

    #Start assembling request data
    data =
        'token': session
        'offset': offset
    
    #Put the query arguments into the request data
    for key, value of query
        data[key] = value
    
    #Make an API call
    request = apiCall url, data
    
    #Link it to the parser
    request.done (data) ->
        dataParseTable data

#Parses retrieved data and loads it in to the table
dataParseTable = (data) ->
    #Get some variables to make life easier later on
    model = root.dataCurrentModel
    modelProps = root.dataConfig['properties'][model]
    tableHead = $ '#data_tableHead'
    tableBody = $ '#data_tableBody'
    
    #Append the checkbox icon cell
    tableHead.append '<td>&nbsp;<span class="glyphicon glyphicon-ok"></span>&nbsp;</td>'
    

#Initialize the console scripting (on ready)
$ initialize