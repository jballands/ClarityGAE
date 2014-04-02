#Establish the root object
root = this

root.session = ''
root.titlebarContracted = '50px'
root.titlebarExpanded = '38%'

#Initialization
$ ->
    #Expand the titlebar back to normal
    ($ "#claritylogobar").css "height", root.titlebarExpanded
    
    #Bind buttons
    ($ "#form_login").submit formSubmit
    ($ "#button_continue").click sessionContinue
    ($ "#button_switch").click sessionSwitch
    
    #Check for an existing session token
    session = $.cookies.get "clarity-console-session"
    root.session = session
    
    #If there is no session token, then show the login controls and return
    if not session
        do ($ "#div_login").show
        return
    
    #Fire off a request to check the session token
    request = apiCall "/api/session_get",
        "id": session
    
    #On fail, clear the cookie and show the login controls
    request.fail ->
        $.cookies.del "clarity-console-session"
        do ($ "#div_login").show
        return
    
    #On success, do some shit
    request.done (data) ->
        
        #If it's closed, clear the cookies, show login, etc.
        if data["closed"]
            do sessionSwitch
            return
        
        #Put a generic message in the text area, and show the continue div
        ($ "#text_continue").text "Welcome back."
        do ($ "#div_continue").show
        
        #Fire off a lazy loader to try and get the provider's name
        lazy = apiCall "/api/provider_get", {"token": root.session, "id": data["user"]}, true
        lazy.done (data) ->
            ($ "#text_continue").html "Welcome back, <strong>#{data['name_first']} #{data['name_last']}</strong>."
            ($ "#button_switch").prop "disabled", false

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
            if not lazy
                bootbox.alert xhr.responseText
        'complete': ->
            if not lazy
                do $('#loader').hide
                $('.load-disable').prop 'disabled', false

formSubmit = ->
    #Get the basic form data
    form_data =
        'console': true
        'username': do ($ "input[name=username]").val
        'password': do ($ "input[name=password]").val
    
    #Start the api call
    request = apiCall "/api/session_begin", form_data
    
    #If the request succeeds, handle the data, animate, and forward
    request.done (data) ->
        $.cookies.set "clarity-console-session", data["token"]
        do sessionContinue
    
    #Return a false to prevent the actual form from doing anything
    return false

sessionContinue = ->
    do ($ "#container").hide
    ($ "#claritylogobar").animate {"height": root.titlebarContracted}, complete = ->
        window.location = "/console"
        return
    return

sessionSwitch = ->
    $.cookies.del "clarity-console-session"
    do ($ "#div_continue").hide
    do ($ "#div_login").show