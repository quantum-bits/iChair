function createSchedule(id, flexibleScheduleToggle, pdfScheduleToggle, paperSize = 'LETTER', 
    scheduleData, showFlexibleSchedule, showPdfSchedule, htmlElementIds = {}) {
    //flexibleToggle = '', spanSwitchToPdf = '', spanSwitchToNormal = '', spanSwitchToLegal = '', spanSwitchToLetter = '') {
    //console.log('show pdf schedule: ', showPdfSchedule);
    console.log(htmlElementIds.toggle+id);
    flexibleToggle = htmlElementIds.toggle+id;
    spanSwitchToPdf = htmlElementIds.pdf+id;
    spanSwitchToNormal = htmlElementIds.normal+id;
    spanSwitchToLegal =  htmlElementIds.legal+id;
    spanSwitchToLetter = htmlElementIds.letter+id;
    //flexibleToggle = "toggle-" + id;
    //spanSwitchToPdf = "span-switch-to-pdf-" + id;
    //spanSwitchToNormal = "span-switch-to-normal-" + id;
    //spanSwitchToLegal = "span-switch-to-legal-" + id;
    //spanSwitchToLetter = "span-switch-to-letter-" + id;

    console.log('show flex schedule: ', showFlexibleSchedule);
    console.log('flexibleScheduleToggle', flexibleScheduleToggle);
    if (flexibleScheduleToggle) {
        showFlexibleSchedule[id] = !showFlexibleSchedule[id];
    }
    console.log('show flex schedule: ', showFlexibleSchedule);
    if (pdfScheduleToggle) {
        showPdfSchedule[id] = !showPdfSchedule[id];
    }

    //console.log(scheduleData);
    //console.log(spanSwitchToPdf, spanSwitchToNormal, spanSwitchToLegal, spanSwitchToLetter);
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Default_parameters
    //let roomData = {{json_room_data|safe}};

    let line_list;
    let filled_row_list;
    let box_list;
    let table_text_list;
    let box_label_list;
    let grid_line_width;
    let grid_line_colour;
  // https://stackoverflow.com/questions/7196212/how-to-create-dictionary-and-add-key-value-pairs-dynamically?rq=1
  // https://stackoverflow.com/questions/9251480/set-canvas-size-using-javascript/9251497
    
    if (showFlexibleSchedule[id]) {
      line_list = scheduleData.grid_list;
      filled_row_list = scheduleData.filled_row_list;
      box_list = scheduleData.box_list;
      table_text_list = scheduleData.table_text_list;
      box_label_list = scheduleData.box_label_list;
      grid_line_width = scheduleData.schedule.grid_line_width;
      grid_line_colour = scheduleData.schedule.grid_line_colour;
      width = scheduleData.schedule.width;
      height = scheduleData.schedule.height;
      //https://www.w3schools.com/jsref/prop_html_innerhtml.asp
      document.getElementById(flexibleToggle).innerHTML = "Switch to Fixed View";
    } else {
      line_list = scheduleData.fixed_size_grid_list;
      filled_row_list = scheduleData.fixed_size_filled_row_list;
      box_list = scheduleData.fixed_size_box_list;
      table_text_list = scheduleData.fixed_size_table_text_list;
      box_label_list = scheduleData.fixed_size_box_label_list;
      grid_line_width = scheduleData.fixed_size_schedule.grid_line_width;
      grid_line_colour = scheduleData.fixed_size_schedule.grid_line_colour;
      width = scheduleData.fixed_size_schedule.width;
      height = scheduleData.fixed_size_schedule.height;
      document.getElementById(flexibleToggle).innerHTML = "Switch to Flexible View";
    }

    if (showPdfSchedule[id]) {
      document.getElementById(spanSwitchToNormal).style.display = "inline-block";
      document.getElementById(spanSwitchToPdf).style.display = "none";
      //document.getElementById("toggle-pdf-"+id).innerHTML = "Stop Printable View";
      if (paperSize === "LEGAL") {
        document.getElementById(spanSwitchToLegal).style.display = "none";
        document.getElementById(spanSwitchToLetter).style.display = "inline-block";
      } else {
        document.getElementById(spanSwitchToLegal).style.display = "inline-block";
        document.getElementById(spanSwitchToLetter).style.display = "none";
      }
    } else {
      document.getElementById(spanSwitchToPdf).style.display = "inline-block";
      document.getElementById(spanSwitchToNormal).style.display = "none";
      document.getElementById(spanSwitchToLegal).style.display = "none";
      document.getElementById(spanSwitchToLetter).style.display = "none";
      //document.getElementById("toggle-pdf-"+id).innerHTML = "Switch to Printable (PDF) View";
    }

    let stream;
    let canvas = document.getElementById(id);
    let iframe = document.getElementById("iframe-"+id);
    let context;
    let scale = 1;
    let topMargin = 0;
    //console.log('id: ', id);
    if (showPdfSchedule[id]) {
      //https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_toggle_hide_show
      //https://allyjs.io/tutorials/hiding-elements.html
      iframe.style.display = "block";
      canvas.style.display = "none";
      //console.log('showing iframe, but not canvas');
      stream = blobStream();
      context = new canvas2pdf.PdfContext(stream, {size: paperSize});
      iframe.width = width;
      iframe.height = height;
      scale = 0.61;
      //console.log('height: ', height);
      // make the top margin a bit smaller if the schedule is long...it's still possible that the schedule will be
      // too long and will go off the bottom of the printed page, though.
      if (height > this.maxHeight) {
        topMargin = 10;
      } else {
        topMargin = 60;
      }
      console.log('top margin: ', topMargin);
    } else {
      // https://allyjs.io/tutorials/hiding-elements.html
      iframe.style.display = "none";
      canvas.style.display = "block";
      //console.log('showing canvas, but not iframe');
      context = canvas.getContext('2d');
      // https://www.w3schools.com/TAGs/tryit.asp?filename=tryhtml5_canvas_height_width_clear
      canvas.width = width;
      canvas.height = height;
    }
    
    for(var n = 0; n < filled_row_list.length; n++) {
      context.beginPath();
      //https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/rect
      context.rect(scale*filled_row_list[n][0], scale*filled_row_list[n][1]+topMargin, scale*filled_row_list[n][2], scale*filled_row_list[n][3]);
      context.fillStyle = filled_row_list[n][4];
      context.fill();
      context.lineWidth = filled_row_list[n][5];
      context.strokeStyle = filled_row_list[n][6];
      context.stroke();
      // From canvas2pdf docs: Calling fill and then stroke consecutively only executes fill;
      // to get around this, I'm constructing the rectangle a second time and only calling stroke the second time
      if (this.showPdfSchedule[id]) {
        context.beginPath();
      //https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/rect
        context.rect(scale*filled_row_list[n][0], scale*filled_row_list[n][1]+topMargin, scale*filled_row_list[n][2], scale*filled_row_list[n][3]);
        context.lineWidth = filled_row_list[n][5];
        context.strokeStyle = filled_row_list[n][6];
        context.stroke();
      }
    }
  
    for(var n = 0; n < line_list.length; n++) {
      context.beginPath();
      context.moveTo(scale*line_list[n][0], scale*line_list[n][1]+topMargin);
      context.lineTo(scale*line_list[n][2], scale*line_list[n][3]+topMargin);
      context.lineWidth = grid_line_width;
      context.strokeStyle = grid_line_colour;
      context.lineCap = 'square';		
      context.stroke();
      }

    for(var n = 0; n < box_list.length; n++) {
      context.beginPath();
      context.rect(scale*box_list[n][0], scale*box_list[n][1]+topMargin, scale*box_list[n][2], scale*box_list[n][3]);
      context.fillStyle = box_list[n][4];
      context.fill();
      context.lineWidth = box_list[n][5];
      context.strokeStyle = box_list[n][6];
      context.stroke();
      // From canvas2pdf docs: Calling fill and then stroke consecutively only executes fill;
      // to get around this, I'm constructing the rectangle a second time and only calling stroke the second time
      // https://jenkov.com/tutorials/html5-canvas/stroke-fill.html
      if (this.showPdfSchedule[id]) {
        context.beginPath();
        context.rect(scale*box_list[n][0], scale*box_list[n][1]+topMargin, scale*box_list[n][2], scale*box_list[n][3]);
        context.lineWidth = box_list[n][5];
        context.strokeStyle = box_list[n][6];
        context.stroke();
      }
    }

    for(var n = 0; n < box_label_list.length; n++) {
      context.textAlign = 'center';
      context.textBaseline = 'middle';		       
      context.fillStyle = box_label_list[n][4];
      if (!this.showPdfSchedule[id]) {
        context.font = box_label_list[n][3];
      } else {
        context.font = "bold 10pt Helvetica";
      }
      // console.log('font: ', box_label_list[n][3]);
      // https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/fillText
      context.fillText(box_label_list[n][2],scale*box_label_list[n][0],scale*box_label_list[n][1]+topMargin);
      }
    
    for(var n = 0; n < table_text_list.length; n++) {
      context.textAlign = 'center';
      context.textBaseline = 'middle';		       
      context.fillStyle = table_text_list[n][4];
      //context.font = table_text_list[n][3];
      if (!this.showPdfSchedule[id]) {
        context.font = table_text_list[n][3];
      } else {
        context.font = "10pt Helvetica";
      }
      context.fillText(table_text_list[n][2],scale*table_text_list[n][0],scale*table_text_list[n][1]+topMargin);
      }
    
    if (showPdfSchedule[id]) {
      context.end();
      context.stream.on('finish', function () {
        iframe.src = context.stream.toBlobURL('application/pdf');
        // not sure what the following does....
        //var blob = ctx.stream.toBlob('application/pdf');
        //saveAs(blob, 'example.pdf', true);
      });
    }
  }