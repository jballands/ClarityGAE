// Generated by CoffeeScript 1.7.1
(function() {
  var apiCall, consoleLogout, dataCreateRecord, dataCreateSubmitRecord, dataDeleteRecords, dataDetailRecord, dataFilterAdd, dataFilterChange, dataFilterRemove, dataInitButtons, dataLoadTable, dataMakeDetailView, dataMakeTableView, dataModalTicketClose, dataPageBack, dataPageButton, dataPageForward, dataParseTable, initialize, root;

  root = this;

  root.dataConfig = {};

  root.dataCurrentModel = '';

  root.dataCurrentID = '';

  root.dataCurrentQuery = {};

  root.dataCurrentOffset = 0;

  root.dataFilters = {};

  root.dataPageTotal = 0;

  root.dataPageMaxResults = 16;

  initialize = function() {
    ($("#consoleLogout")).click(consoleLogout);
    ($("#data_buttonDeleteRecord")).click(dataDeleteRecords);
    ($("#data_buttonCreateRecord")).click(dataCreateRecord);
    ($("#data_buttonCreateRecordSubmit")).click(dataCreateSubmitRecord);
    ($("#data_buttonRefresh")).click(function() {
      return dataLoadTable();
    });
    ($("#data_filterSelect")).change(dataFilterChange);
    ($("#data_buttonFilter")).click(function() {
      return dataFilterAdd();
    });
    ($("#data_modalTicketClose")).click(dataModalTicketClose);
    ($('#data_modalDetail')).on("hidden.bs.modal", function() {
      return dataLoadTable();
    });
    ($('#data_modalCreateRecord')).on("hidden.bs.modal", function() {
      return dataLoadTable();
    });
    ($("#data_filterText")).hide();
    ($("#data_filterValue")).hide();
    $('.load-disable').prop('disabled', true);
    return (apiCall('/static/data/data-config.json', {}, true, "GET")).done(function(data) {
      root.dataConfig = data;
      return dataInitButtons();
    });
  };

  consoleLogout = function() {
    $.cookies.del("clarity-console-session");
    return window.location = "/";
  };

  apiCall = function(url, data, lazy, method, context) {
    if (data == null) {
      data = {};
    }
    if (lazy == null) {
      lazy = false;
    }
    if (method == null) {
      method = 'POST';
    }
    if (context == null) {
      context = document.body;
    }
    if (!lazy) {
      $('.load-disable').prop('disabled', true);
      $('#loader').show();
    }
    return $.ajax({
      'url': url,
      'type': method,
      'contentType': 'application/json; charset=utf-8',
      'dataType': 'json',
      'context': context,
      'data': JSON.stringify(data),
      'error': function(xhr, status, error) {
        var message;
        if (!lazy && xhr && error) {
          message = xhr.responseText || error;
          if (message === !null && message === !void 0) {
            return bootbox.alert(message);
          }
        }
      },
      'complete': function() {
        if (!lazy) {
          $('#loader').hide();
          return $('.load-disable').prop('disabled', false);
        }
      }
    });
  };

  dataInitButtons = function() {
    var button, markup, model, modelName, _i, _len, _ref;
    $('#data_buttonRow .btn').remove();
    _ref = root.dataConfig['models'];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      model = _ref[_i];
      modelName = root.dataConfig['names'][model];
      markup = "<label class='btn btn-primary load-disable'><input type='radio'>" + modelName + "</label>";
      button = $(markup).appendTo($('#data_buttonRow'));
      button.data('model', model);
      button.click(function() {
        root.dataCurrentOffset = 0;
        return dataLoadTable($(this).data('model'));
      });
    }
    $('#data_buttonRow .btn').button();
  };

  dataLoadTable = function(model, query, offset) {
    var data, key, request, url, value;
    if (model == null) {
      model = root.dataCurrentModel;
    }
    if (query == null) {
      query = root.dataCurrentQuery;
    }
    if (offset == null) {
      offset = root.dataCurrentOffset;
    }
    ($('#data_tableHead')).children().remove();
    ($('#data_tableBody')).children().remove();
    ($("#data_pagination")).children().remove();
    if (model === !root.dataCurrentModel) {
      root.dataFilters = {};
      ($("data_filterList")).children().remove();
    }
    root.dataCurrentModel = model;
    url = "/api/" + model + "_query";
    data = {
      'token': session,
      'offset': offset,
      'limit': root.dataPageMaxResults
    };
    data = $.extend(data, root.dataFilters);
    for (key in query) {
      value = query[key];
      data[key] = value;
    }
    request = apiCall(url, data);
    return request.done(function(data) {
      return dataParseTable(data);
    });
  };

  dataParseTable = function(data) {
    var button, cell, checkbox, container, current, entry, i, instance, link, link_back, link_forward, model, modelProps, option, pages, prop, property, row, selector, tableBody, tableHead, _i, _j, _k, _l, _len, _len1, _len2, _len3, _m, _ref, _ref1, _results;
    model = root.dataCurrentModel;
    modelProps = root.dataConfig['properties'][model];
    tableHead = $('#data_tableHead');
    tableBody = $('#data_tableBody');
    tableHead.append('<th>&nbsp;<span class="glyphicon glyphicon-ok"></span>&nbsp;</th>');
    for (_i = 0, _len = modelProps.length; _i < _len; _i++) {
      prop = modelProps[_i];
      if (!prop['inTable']) {
        continue;
      }
      tableHead.append("<th><small>" + prop['name'] + "</small></th>");
    }
    tableHead.append("<th></th>");
    _ref = data['results'];
    for (_j = 0, _len1 = _ref.length; _j < _len1; _j++) {
      instance = _ref[_j];
      row = ($("<tr></tr>")).appendTo(tableBody);
      row.data('id', instance['id']);
      cell = ($("<td></td>")).appendTo(row);
      checkbox = ($("<input type='checkbox' class='data_tableCheck'>")).appendTo(cell);
      checkbox.data("id", instance["id"]);
      for (_k = 0, _len2 = modelProps.length; _k < _len2; _k++) {
        prop = modelProps[_k];
        if (!prop['inTable']) {
          continue;
        }
        cell = ($("<td></td>")).appendTo(row);
        dataMakeTableView(prop, instance, cell);
      }
      cell = ($("<td></td>")).appendTo(row);
      button = ($("<button class='btn btn-success btn-xs btn-block'>VIEW / EDIT</button>")).appendTo(cell);
      button.data('model', model);
      button.data('id', instance["id"]);
      button.click(function() {
        return dataDetailRecord(($(this)).data("model"), ($(this)).data("id"));
      });
    }
    container = $('#data_pagination');
    pages = Math.ceil(data["count"] / root.dataPageMaxResults);
    current = Math.floor(root.dataCurrentOffset / root.dataPageMaxResults);
    root.dataPageTotal = pages;
    if (pages > 1) {
      link_back = ($('<li><a href="#">&laquo;</a></li>')).appendTo(container);
      link_back.click(dataPageBack);
      for (i = _l = 0, _ref1 = pages - 1; 0 <= _ref1 ? _l <= _ref1 : _l >= _ref1; i = 0 <= _ref1 ? ++_l : --_l) {
        entry = ($('<li></li>')).appendTo(container);
        link = ($('<a href="#"></a>')).appendTo(entry);
        link.attr('offset', i * dataPageMaxResults);
        link.text(i + 1);
        if (i === current) {
          entry.addClass('active');
        }
        link.click(dataPageButton);
      }
      link_forward = ($('<li><a href="#">&raquo;</a></li>')).appendTo(container);
      link_forward.click(dataPageForward);
    }
    ($('#data_filterSelect>option:enabled')).remove();
    ($("#data_filterSelect>option:disabled")).attr("selected", true);
    ($("#data_filterText")).hide();
    ($("#data_filterValue")).hide();
    selector = $('#data_filterSelect');
    _results = [];
    for (_m = 0, _len3 = modelProps.length; _m < _len3; _m++) {
      property = modelProps[_m];
      if (!property["inFilter"]) {
        continue;
      }
      option = ($('<option></option>')).appendTo(selector);
      option.val(property['name']);
      _results.push(option.text(property['name']));
    }
    return _results;
  };

  dataMakeTableView = function(property, instance, cell) {
    var button, model, name, option, options, request, value, _i, _len;
    name = property["name"];
    value = instance[name];
    if (typeof value === "boolean") {
      value = JSON.stringify(value);
    }
    if (!value) {
      cell.append("<em>Empty</em>");
      return;
    }
    switch (property["type"]) {
      case "headshot":
        if (!value) {
          cell.append("<span class='glyphicon glyphicon-remove'></span>");
          return;
        }
        button = ($("<button class='btn btn-sm btn-success'><span class='glyphicon glyphicon-picture'></span></button>")).appendTo(cell);
        button.data("href", "/api/headshot_download?token=" + session + "&id=" + value);
        button.click(function() {
          var href;
          href = ($(this)).data("href");
          return bootbox.alert("<div class='text-center'><h2>Headshot</h2><hr><img src='" + href + "'></div>");
        });
        return;
      case "model":
        model = property["model"];
        button = ($("<button class='btn btn-success btn-xs btn-block' disabled>. . .</button>")).appendTo(cell);
        button.data("model", model);
        button.data("id", instance[name]);
        button.click(function() {
          return dataDetailRecord(($(this)).data("model"), ($(this)).data("id"));
        });
        request = apiCall("/api/" + model + "_get", {
          "token": session,
          "id": instance[name]
        }, true);
        request.done(function() {
          return button.prop("disabled", false);
        });
        switch (model) {
          case "client":
            request.done(function(data) {
              return button.text("" + data['name_first'] + " " + data['name_last']);
            });
            break;
        }
        return;
      case "qrcode":
        button = ($("<button class='btn btn-sm btn-success'><span class='glyphicon glyphicon-qrcode'></span></button>")).appendTo(cell);
        button.data("data", value);
        button.click(function() {
          var markup;
          button = $(this);
          markup = "<div class='text-center'><h2>View QR Code</h2><hr><img class='qrcode'></div>";
          bootbox.alert(markup);
          return setTimeout(function() {
            return qr.image({
              "image": ($("img.qrcode")).get(0),
              "value": button.data("data"),
              "size": 100
            });
          }, 200);
        });
        return;
      case "select":
        options = property["options"];
        for (_i = 0, _len = options.length; _i < _len; _i++) {
          option = options[_i];
          if (option["value"] === value) {
            value = option["text"];
            break;
          }
        }
        break;
    }
    return cell.append(value);
  };

  dataDetailRecord = function(model, modelID) {
    var request;
    ($('#data_modalDetailTable')).children().each(function() {
      return ($(this)).remove();
    });
    root.dataCurrentID = modelID;
    request = apiCall("/api/" + model + "_get", {
      "token": session,
      "id": modelID
    });
    return request.done(function(data) {
      var cell, modelProps, prop, row, table, _i, _len;
      table = $("#data_modalDetailTable");
      modelProps = root.dataConfig["properties"][model];
      for (_i = 0, _len = modelProps.length; _i < _len; _i++) {
        prop = modelProps[_i];
        if (!prop["inDetail"]) {
          continue;
        }
        row = ($("<tr></tr>")).appendTo(table);
        row.append("<td><strong>" + prop['name'] + "</strong></td>");
        cell = ($("<td></td>")).appendTo(row);
        dataMakeDetailView(model, prop, data, cell);
      }
      ($(".data_modalDetailWell")).hide();
      ($(".data_modalDetailWell[model=" + model + "]")).show();
      return ($('#data_modalDetail')).modal('show');
    });
  };

  dataMakeDetailView = function(model, property, instance, cell, empty) {
    var button, editor, instanceID, linkedID, name, options, request, type, url, value, _i, _len;
    if (empty == null) {
      empty = false;
    }
    name = property["name"];
    type = property["type"];
    if (empty) {
      instanceID = null;
      value = null;
    } else {
      instanceID = instance["id"];
      value = instance[name];
    }
    if (typeof value === 'boolean') {
      value = JSON.stringify(value);
    }
    editor = $("<a href='#'></a>").appendTo(cell);
    url = "/api/" + model + "_consoleupdate";
    options = {
      "name": name,
      "type": type,
      "url": url,
      "pk": instanceID,
      "value": value,
      "token": session
    };
    switch (type) {
      case "readonly":
        editor.remove();
        cell.append(value);
        return;
      case 'select':
        options['source'] = property["options"];
        break;
      case 'password':
        options['emptytext'] = 'Click to Change';
        break;
      case 'textarea':
        options['display'] = function(value, sourceData) {
          if (value.length > 0) {
            return ($(this)).text('. . .');
          }
        };
        break;
      case 'combodate':
        options['format'] = 'YYYY-MM-DD';
        options['inputclass'] = 'input-sm';
        options['combodate'] = {
          'minYear': 1900,
          'maxYear': new Date().getFullYear()
        };
        break;
      case "model":
        options["type"] = "text";
        break;
      case 'modelList':
        editor.remove();
        if (value.length === 0) {
          cell.append("<em>Empty</em>");
        }
        for (_i = 0, _len = value.length; _i < _len; _i++) {
          linkedID = value[_i];
          button = ($("<button class='btn btn-success btn-xs btn-block' disabled>. . .</button>")).appendTo(cell);
          button.data("model", property["model"]);
          button.data("id", linkedID);
          button.click(function() {
            return dataDetailRecord(($(this)).data("model"), ($(this)).data("id"));
          });
          request = apiCall("/api/" + property['model'] + "_get", {
            "token": session,
            "id": linkedID
          }, true, 'POST', button);
          request.done(function(data) {
            ($(this)).prop("disabled", false);
            switch (($(this)).data("model")) {
              case "ticket":
                ($(this)).text("Opened: " + data['opened']);
                break;
            }
          });
        }
        return;
      case "qrcode":
        if (!empty) {
          return dataMakeTableView(property, instance, cell);
        }
        options["type"] = "text";
    }
    return editor.editable(options);
  };

  dataPageBack = function() {
    root.dataCurrentOffset -= root.dataPageMaxResults;
    if (root.dataCurrentOffset < 0) {
      root.dataCurrentOffset = 0;
    }
    return dataLoadTable();
  };

  dataPageForward = function() {
    root.dataCurrentOffset += root.dataPageMaxResults;
    if (root.dataCurrentOffset === root.dataPageMaxResults * root.dataPageTotal) {
      root.dataCurrentOffset = root.dataPageMaxResults * (root.dataPageTotal - 1);
    }
    return dataLoadTable();
  };

  dataPageButton = function() {
    root.dataCurrentOffset = ($(this)).attr("offset");
    return dataLoadTable();
  };

  dataDeleteRecords = function() {
    var checkedIDs, request;
    checkedIDs = [];
    ($(".data_tableCheck:checked")).each(function() {
      return checkedIDs.push(($(this)).data("id"));
    });
    if (checkedIDs.length === 0) {
      return;
    }
    request = apiCall("/api/" + root.dataCurrentModel + "_remove", {
      "token": session,
      "ids": checkedIDs
    });
    return request.always(function() {
      return dataLoadTable();
    });
  };

  dataCreateRecord = function() {
    var cell, model, prop, properties, row, table, _i, _len;
    table = $("#data_modalCreateRecordTable");
    table.children().each(function() {
      return ($(this)).remove();
    });
    model = root.dataCurrentModel;
    properties = root.dataConfig["properties"][model];
    for (_i = 0, _len = properties.length; _i < _len; _i++) {
      prop = properties[_i];
      if (!prop["inCreate"]) {
        continue;
      }
      row = ($("<tr></tr>")).appendTo(table);
      if (prop["required"]) {
        ($("<td><strong>" + prop['name'] + "</strong></td>")).appendTo(row);
      } else {
        ($("<td>" + prop['name'] + "</td>")).appendTo(row);
      }
      cell = ($("<td></td>")).appendTo(row);
      cell.data("name", prop["name"]);
      dataMakeDetailView(model, prop, null, cell, true);
    }
    return ($("#data_modalCreateRecord")).modal("show");
  };

  dataCreateSubmitRecord = function() {
    var data, editable, editables, request, value, _i, _len;
    editables = ($("#data_modalCreateRecord")).find(".editable");
    data = {};
    for (_i = 0, _len = editables.length; _i < _len; _i++) {
      editable = editables[_i];
      value = ($(editable)).editable("getValue");
      data = $.extend({}, data, value);
    }
    data["token"] = session;
    ($("#data_buttonCreateRecordSubmit")).prop("disabled", true);
    request = apiCall("/api/" + root.dataCurrentModel + "_create", data);
    return request.done(function() {
      ($("#data_modalCreateRecord")).modal("hide");
      return ($("#data_buttonCreateRecordSubmit")).prop("disabled", false);
    });
  };

  dataModalTicketClose = function() {
    var request;
    request = apiCall("/api/ticket_close", {
      "token": session,
      "id": root.dataCurrentID
    }, true);
    return request.always(function() {
      return ($('#data_modalDetail')).modal('hide');
    });
  };

  dataFilterChange = function() {
    var entry, name, obj, option, property, select, _i, _j, _len, _len1, _ref, _ref1;
    name = ($(this)).val();
    select = false;
    property = null;
    _ref = root.dataConfig["properties"][root.dataCurrentModel];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      obj = _ref[_i];
      if (obj["name"] === name) {
        select = obj["type"] === "select";
        property = obj;
        break;
      }
    }
    if (select) {
      ($("#data_filterValue > option:enabled")).remove();
      _ref1 = property["options"];
      for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
        option = _ref1[_j];
        entry = ($('<option></option>')).appendTo($("#data_filterValue"));
        entry.val(option["value"]);
        entry.text(option["text"]);
      }
      ($("#data_filterText")).hide();
      ($("#data_filterValue")).show();
      return;
    }
    ($("#data_filterText")).val("");
    ($("#data_filterText")).show();
    return ($("#data_filterValue")).hide();
  };

  dataFilterAdd = function(given_name, given_value) {
    var button, entry, field, select, text, value;
    if (given_name == null) {
      given_name = null;
    }
    if (given_value == null) {
      given_value = null;
    }
    field = "";
    value = "";
    text = "";
    if (!given_name) {
      field = ($("#data_filterSelect")).val();
      if (!field) {
        return bootbox.alert("You must select a field to filter by.");
      }
      select = ($("#data_filterText")).is(":hidden");
      if (select) {
        value = ($("#data_filterValue > option:selected")).val();
        text = ($("#data_filterValue > option:selected")).text();
      } else {
        value = ($("#data_filterText")).val();
        text = value;
      }
      if (!value) {
        return bootbox.alert("You must enter or select a field value to filter by.");
      }
    } else {
      field = given_name;
      value = given_value;
      text = value;
    }
    if (root.dataFilters[field]) {
      return bootbox.alert("Filter for this field already exists. Please remove it and try again.");
    }
    entry = ($("<p><strong>" + field + "</strong> = <strong>" + text + "</strong></p>")).appendTo($("#data_filterList"));
    entry.attr("id", "data_filter_" + field);
    button = ($("<button class='btn btn-xs btn-danger pull-right'>X</button>")).appendTo(entry);
    button.data("name", field);
    button.click(function() {
      return dataFilterRemove(($(this)).data("name"));
    });
    root.dataFilters[field] = value;
    return dataLoadTable();
  };

  dataFilterRemove = function(name) {
    delete root.dataFilters[name];
    ($("#data_filter_" + name)).remove();
    return dataLoadTable();
  };

  $(initialize);

}).call(this);
