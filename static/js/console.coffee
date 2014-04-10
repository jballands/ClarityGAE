root = this

#Console variables
root.dataConfig = {}

root.dataCurrentModel = ''
root.dataCurrentID = ''
root.dataCurrentQuery = {}
root.dataCurrentOffset = 0

root.dataAdvancedMode = false
root.dataFilters = {}
root.dataPageTotal = 0
#root.dataCurrentOffset = 0
root.dataPageMaxResults = 16
#END Console variables

initialize = ->
    #Bind the buttons
    ($ "#consoleLogout").click consoleLogout
    ($ "#data_buttonDeleteRecord").click dataDeleteRecords
    ($ "#data_buttonCreateRecord").click dataCreateRecord
    ($ "#data_buttonCreateRecordSubmit").click dataCreateSubmitRecord
    ($ "#data_buttonRefresh").click -> do dataLoadTable
    
    #Bind the filter shit
    ($ "#data_radioNormal").click dataModeNormal
    ($ "#data_radioAdvanced").click dataModeAdvanced
    ($ "#data_filterSelect").change dataFilterChange
    ($ "#data_buttonFilter").click -> do dataFilterAdd
    ($ "#data_buttonQuery").click -> do dataLoadTable
    
    #Modal buttons that are model-specific
    ($ "#data_modalTicketClose").click dataModalTicketClose
    
    #Bind some events
    ($ '#data_modalDetail').on "hidden.bs.modal", -> do dataLoadTable
    ($ '#data_modalCreateRecord').on "hidden.bs.modal", -> do dataLoadTable
    
    #Hide filter entry fields
    do ($ "#data_filterText").hide
    do ($ "#data_filterValue").hide
    
    #Disable any stragglers
    $('.load-disable').prop 'disabled', true
    (apiCall '/static/data/data-config.json', {}, true, "GET").done (data) ->
        root.dataConfig = data
        do dataInitButtons

consoleLogout = ->
    $.cookies.del "clarity-console-session"
    window.location = "/"

#Api call method for stadardizing api calls :D
apiCall = (url, data={}, lazy=false, method='POST', context=document.body) ->
    if not lazy
        #Disable elements that are marked to be
        $('.load-disable').prop 'disabled', true

        #Show that spiffy loader sprite
        do $('#loader').show
    
    #Start that AJAX up
    return $.ajax
        'url': url
        'type': method
        'contentType': 'application/json; charset=utf-8'
        'dataType': 'json'
        'context': context
        'data': JSON.stringify data
        'error': (xhr, status, error) ->
            if not lazy and xhr and error
                message = xhr.responseText or error
                if message
                    bootbox.alert message
        'complete': ->
            if not lazy
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
            #Clear page offset
            root.dataCurrentOffset = 0
            dataLoadTable $(this).data('model')
    do $('#data_buttonRow .btn').button
    return

#Calls the api, and passes the data to the parser
dataLoadTable = (model = root.dataCurrentModel, query = root.dataCurrentQuery, offset = root.dataCurrentOffset) ->
    #Clear the table and pagination
    do ($ '#data_tableHead').children().remove
    do ($ '#data_tableBody').children().remove
    do ($ "#data_pagination").children().remove
    
    #If the model changes, clear filters
    if model is not root.dataCurrentModel
        root.dataFilters = {}
        do ($ "#data_filterList").children().remove
        ($ "#data_queryText").val ""
    
    #Set it again, so the parser can see changes
    root.dataCurrentModel = model
    
    #Construct a url
    url = "/api/#{model}_search"

    #Start assembling request data
    data =
        'token': session
        'offset': offset
        'limit': root.dataPageMaxResults
    
    #If advanced mode, only insert the query string, else insert the filters
    if root.dataAdvancedMode
        data["query"] = ($ "#data_queryText").val()
    else
        data = $.extend data, root.dataFilters
    
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
    #alert JSON.stringify(data)
    #Get some variables to make life easier later on
    model = root.dataCurrentModel
    modelProps = root.dataConfig['properties'][model]
    tableHead = $ '#data_tableHead'
    tableBody = $ '#data_tableBody'
    
    #Append the checkbox icon cell
    tableHead.append '<th>&nbsp;<span class="glyphicon glyphicon-ok"></span>&nbsp;</th>'
    
    #Put in the property headers
    for prop in modelProps
        continue if not prop['inTable']
        tableHead.append "<th><small>#{prop['name']}</small></th>"
    
    #Put in an empty header for the edit button column
    tableHead.append "<th></th>"
    
    #Iterate through instances passed via data and insert all their shit
    for instance in data['results']
        row = ($ "<tr></tr>").appendTo tableBody
        row.data 'id', instance['id']
        
        #Insert checkbox
        cell = ($ "<td></td>").appendTo row
        checkbox = ($ "<input type='checkbox' class='data_tableCheck'>").appendTo cell
        checkbox.data "id", instance["id"]
        
        for prop in modelProps
            continue if not prop['inTable']
            cell = ($ "<td></td>").appendTo row
            dataMakeTableView prop, instance, cell
        
        #Insert edit button
        cell = ($ "<td></td>").appendTo row
        button = ($ "<button class='btn btn-success btn-xs btn-block'>VIEW / EDIT</button>").appendTo cell
        button.data 'model', model
        button.data 'id', instance["id"]
        button.click ->
            dataDetailRecord ($ this).data("model"), ($ this).data("id")
    
    #Build the pagination buttons
    container = $ '#data_pagination'
    pages = Math.ceil(data["count"] / root.dataPageMaxResults)
    current = Math.floor(root.dataCurrentOffset / root.dataPageMaxResults)

    #Store the total page count for future reference
    root.dataPageTotal = pages

    #If there's only one page, there's no need for pagination
    if pages > 1
        #Insert back button and link it to its function
        link_back = ($ '<li><a href="#">&laquo;</a></li>').appendTo container
        link_back.click dataPageBack

        for i in [0 .. pages - 1]
            entry = ($ '<li></li>').appendTo container
            link = ($ '<a href="#"></a>').appendTo entry

            link.attr 'offset', (i * dataPageMaxResults)
            link.text i + 1

            if i is current
                entry.addClass 'active'

            #Link the button to its function
            link.click(dataPageButton);

        #Insert forward button and link it to its function
        link_forward = ($ '<li><a href="#">&raquo;</a></li>').appendTo container
        link_forward.click dataPageForward

    #Remove all the filter fields from the selection dropdown and hide the entry fields
    do ($ '#data_filterSelect>option:enabled').remove
    ($ "#data_filterSelect>option:disabled").attr "selected", true
    do ($ "#data_filterText").hide
    do ($ "#data_filterValue").hide

    #Insert filter options for the current model
    selector = $ '#data_filterSelect'
    for property in modelProps
        continue if not property["inFilter"]
        option = ($ '<option></option>').appendTo selector
        option.val property['name']
        option.text property['name']

dataMakeTableView = (property, instance, cell) ->
    name = property["name"]
    value = instance[name]
    
    #If boolean, set value to stringified boolean
    if typeof value is "boolean"
        value = JSON.stringify value
    
    #If empty, just make the table say empty :P
    if not value
        cell.append "<em>Empty</em>"
        return
    
    #Switch based on property name (for specialized types)
    switch property["type"]
        
        #Button to open a bootbox alert with the image inside
        when "headshot"
            #If no headshot, insert an X glyphicon
            if not value
                cell.append "<span class='glyphicon glyphicon-remove'></span>"
                return
            
            button = ($ "<button class='btn btn-sm btn-success'><span class='glyphicon glyphicon-picture'></span></button>").appendTo cell
            button.data "href", "/api/headshot_download?token=#{session}&id=#{value}"
            button.click ->
                href = ($ this).data "href"
                bootbox.alert "<div class='text-center'><h2>Headshot</h2><hr><img src='#{href}'></div>"
            return
        
        #For linking other models
        when "model"
            model = property["model"]
            button = ($ "<button class='btn btn-success btn-xs btn-block' disabled>. . .</button>").appendTo cell
            button.data "model", model
            button.data "id", instance[name]
            
            #Link the button
            button.click ->
                dataDetailRecord ($ this).data("model"), ($ this).data("id")
            
            #Create a lazy loader for the button
            request = apiCall "/api/#{model}_get",
                "token": session
                "id": instance[name],
                true
            request.done -> button.prop "disabled", false
            
            #Switch for button behavior after loading
            switch model
                when "client"
                    request.done (data) -> button.text "#{data['name_first']} #{data['name_last']}"
                    break
            
            return
        
        #For linking and creating qr codes
        when "qrcode"
            button = ($ "<button class='btn btn-sm btn-success'><span class='glyphicon glyphicon-qrcode'></span></button>").appendTo cell
            button.data "data", value
            button.click ->
                button = ($ this)
                markup = "<div class='text-center'><h2>View QR Code</h2><hr><img class='qrcode'></div>"
                bootbox.alert(markup)
                setTimeout ->
                    qr.image
                        "image": ($ "img.qrcode").get 0
                        "value": button.data "data"
                        "size": 100
                , 200
            return
        
        when "select"
            options = property["options"]
            for option in options
                if option["value"] == value
                    value = option["text"]
                    break
            break
    
    #If the value doesn't need special attention, just put the raw data in the table
    cell.append value

dataDetailRecord = (model, modelID) ->
    #Clear the modal's contents
    ($ '#data_modalDetailTable').children().each ->
        do ($ this).remove
    
    root.dataCurrentID = modelID
    
    #Create a non-lazy loader for loading the instance
    request = apiCall "/api/#{model}_get",
        "token": session
        "id": modelID
    
    request.done (data) ->
        #Load some variables up
        table = ($ "#data_modalDetailTable")
        modelProps = root.dataConfig["properties"][model]
        
        #Iterate through props and put 'em all in the table
        for prop in modelProps
            continue if not prop["inDetail"]
            row = ($ "<tr></tr>").appendTo table
            
            #Insert label cell
            row.append "<td><strong>#{prop['name']}</strong></td>"
            
            #Put in a cell and pass it to the factory
            cell = ($ "<td></td>").appendTo row
            dataMakeDetailView model, prop, data, cell
        
        #Hide all model-specific wells
        do ($ ".data_modalDetailWell").hide
        
        #Show the specific one we want (if it exists)
        do ($ ".data_modalDetailWell[model=#{model}]").show
        
        #Show the modal
        ($ '#data_modalDetail').modal 'show'
            
            
            

dataMakeDetailView = (model, property, instance, cell, empty = false) ->
    name = property["name"]
    type = property["type"]
    
    if empty
        instanceID = null
        value = null
    else
        instanceID = instance["id"]
        value = instance[name]
    
    if typeof(value) is 'boolean'
        value = JSON.stringify value
    
    #Start assembling the x-editable thingy
    editor = $( "<a href='#'></a>").appendTo cell
    url = "/api/#{model}_consoleupdate"
    options =
        "name": name
        "type": type
        "url": url
        "pk": instanceID
        "value": value
        "token": session
    
    #Switch the type for specialty types
    switch type
        
        when "readonly"
            do editor.remove
            cell.append value
            return
        
        when 'select'
            options['source'] = property["options"]
            break

        when 'password'
            options['emptytext'] = 'Click to Change'
            break

        when 'textarea'
            options['display'] = (value, sourceData) ->
                if value.length > 0
                    ($ this).text '. . .'
            break

        when 'combodate'
            options['format'] = 'YYYY-MM-DD'
            options['inputclass'] = 'input-sm'
            options['combodate'] =
                'minYear': 1900
                'maxYear': new Date().getFullYear()
            break
        
        when "model"
            options["type"] = "text"
            break
        
        when 'modelList'
            do editor.remove
            #If there aren't any linked models, insert "Empty"
            if value.length is 0
                cell.append "<em>Empty</em>"
            
            #Create a button for each linked ID
            for linkedID in value
                #Create the button
                button = ($ "<button class='btn btn-success btn-xs btn-block' disabled>. . .</button>").appendTo cell
                #cell.append "<br>"
                button.data "model", property["model"]
                button.data "id", linkedID
                button.click ->
                    dataDetailRecord ($ this).data("model"), ($ this).data("id")
                
                #Start the lazy loader
                request = apiCall "/api/#{property['model']}_get",
                    "token": session
                    "id": linkedID,
                    true,
                    'POST',
                    button
                
                #Re-enable the button if the request succeeds
                request.done (data) ->
                    ($ this).prop "disabled", false

                    #Switch for the model type to determine the button's text
                    switch ($ this).data "model"
                        when "ticket"
                            ($ this).text "Opened: #{data['opened']}"
                            break
                
            return
        
        when "qrcode"
            if not empty
                return dataMakeTableView property, instance, cell
            options["type"] = "text"
                
    
    #Initialize the x-editable
    editor.editable options

dataPageBack = ->
    root.dataCurrentOffset -= root.dataPageMaxResults
    if root.dataCurrentOffset < 0
        root.dataCurrentOffset = 0
    do dataLoadTable

dataPageForward = ->
    root.dataCurrentOffset += root.dataPageMaxResults
    if root.dataCurrentOffset is root.dataPageMaxResults * root.dataPageTotal
        root.dataCurrentOffset = root.dataPageMaxResults * (root.dataPageTotal - 1)
    do dataLoadTable

dataPageButton = ->
    root.dataCurrentOffset = ($ this).attr "offset"
    do dataLoadTable

dataDeleteRecords = ->
    #Get a list of checked IDs
    checkedIDs = []
    ($ ".data_tableCheck:checked").each ->
        checkedIDs.push ($ this).data("id")
    
    #If nothing's checked, just return
    return if checkedIDs.length is 0
    
    #Start the request
    request = apiCall "/api/#{root.dataCurrentModel}_remove",
        "token": session
        "ids": checkedIDs
    
    #On success, reload
    request.always -> do dataLoadTable

dataCreateRecord = ->
    table = ($ "#data_modalCreateRecordTable")
    
    #Clear the modal's contents
    table.children().each ->
        do ($ this).remove
    
    #Create a quick reference to the current model
    model = root.dataCurrentModel
    
    #Load the model properties
    properties = root.dataConfig["properties"][model]
    
    #Iterate over and put them in the modal
    for prop in properties
        continue if not prop["inCreate"]
        row = ($ "<tr></tr>").appendTo table
        
        #If required, make it bold
        if prop["required"]
            ($ "<td><strong>#{prop['name']}</strong></td>").appendTo row
        else
            ($ "<td>#{prop['name']}</td>").appendTo row
        
        cell = ($ "<td></td>").appendTo row
        cell.data "name", prop["name"]
        dataMakeDetailView model, prop, null, cell, true
    
    #Show the modal
    ($ "#data_modalCreateRecord").modal "show"

dataCreateSubmitRecord = ->
    #Get all x-editable elements in the modal table
    editables = ($ "#data_modalCreateRecord").find ".editable"
    
    #Empty hash for storing data
    data = {}
    
    #Iterate through each editable and dump its info into the hash
    for editable in editables
        #name = ($ editable).parent().data "name"
        value = ($ editable).editable "getValue"
        #data[name] = value
        data = $.extend {}, data, value
    
    data["token"] = session
    
    #Make the call
    ($ "#data_buttonCreateRecordSubmit").prop "disabled", true
    request = apiCall "/api/#{root.dataCurrentModel}_create", data
    request.done ->
        ($ "#data_modalCreateRecord").modal "hide"
        ($ "#data_buttonCreateRecordSubmit").prop "disabled", false
    
dataModalTicketClose = ->
    request = apiCall "/api/ticket_close",
        "token": session
        "id": root.dataCurrentID,
        true
    request.always ->
        ($ '#data_modalDetail').modal 'hide'

dataFilterChange = ->
    #Get the name of the selected property
    name = do ($ this).val
    
    #If the property is a select type, show the select thingy, hide the text thingy, and insert thingies
    select = false
    property = null
    for obj in root.dataConfig["properties"][root.dataCurrentModel]
        if obj["name"] is name
            select = obj["type"] is "select"
            property = obj
            break
    
    if select
        do ($ "#data_filterValue > option:enabled").remove
        for option in property["options"]
            entry = ($ '<option></option>').appendTo ($ "#data_filterValue")
            entry.val option["value"]
            entry.text option["text"]
        do ($ "#data_filterText").hide
        do ($ "#data_filterValue").show
        return
    
    ($ "#data_filterText").val ""
    do ($ "#data_filterText").show
    do ($ "#data_filterValue").hide

dataFilterAdd = (given_name = null, given_value = null) ->
    field = ""
    value = ""
    text = ""
    
    if not given_name
        #Get the selected field, if none selected, flash an error message
        field = do ($ "#data_filterSelect").val
        return bootbox.alert "You must select a field to filter by." if not field

        #Determine if we're using the select input
        select = ($ "#data_filterText").is ":hidden"

        #Retrieve the values from whichever entry method is relevant
        if select
            value = do ($ "#data_filterValue > option:selected").val
            text = do ($ "#data_filterValue > option:selected").text
        else
            value = do ($ "#data_filterText").val
            text = value

        #If no value given, throw an error
        return bootbox.alert "You must enter or select a field value to filter by." if not value
    
    else
        field = given_name
        value = given_value
        text = value
    
    #Check to see if it's already in the filter list
    return bootbox.alert "Filter for this field already exists. Please remove it and try again." if root.dataFilters[field]
    
    #Put this into the html filter list
    entry = ($ "<p><strong>#{field}</strong> = <strong>#{text}</strong></p>").appendTo ($ "#data_filterList")
    entry.attr "id", "data_filter_#{field}"
    button = ($ "<button class='btn btn-xs btn-danger pull-right'>X</button>").appendTo entry
    button.data "name", field
    button.click ->
        dataFilterRemove ($ this).data("name")
    
    #Put this into the js filter list
    root.dataFilters[field] = value
    
    #Reload table
    do dataLoadTable

dataFilterRemove = (name) ->
    delete root.dataFilters[name]
    do ($ "#data_filter_#{name}").remove
    do dataLoadTable

dataModeNormal = ->
    do ($ "#data_divModeNormal").show
    do ($ "#data_divModeAdvanced").hide
    ($ "#data_queryText").val ""
    root.dataAdvancedMode = false
    do dataLoadTable

dataModeAdvanced = ->
    do ($ "#data_divModeNormal").hide
    do ($ "#data_divModeAdvanced").show
    root.dataFilters = {}
    do ($ "data_filterList").children().remove
    root.dataAdvancedMode = true
    do dataLoadTable

#Initialize the console scripting (on ready)
$ initialize