function createSchedule(id, flexibleScheduleToggle, pdfScheduleToggle, paperSize = 'LETTER', 
    scheduleData, showFlexibleSchedule, showPdfSchedule, htmlElementIds = {}) {
    //flexibleToggle = '', spanSwitchToPdf = '', spanSwitchToNormal = '', spanSwitchToLegal = '', spanSwitchToLetter = '') {
    //console.log('show pdf schedule: ', showPdfSchedule);
    console.log(htmlElementIds.toggle+id);
    flexibleToggle = htmlElementIds.toggle === null ? null : htmlElementIds.toggle+id;
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
    let oneInch = 72;

    let stream;
    let canvas = document.getElementById(id);
    let iframe = document.getElementById("iframe-"+id);
    let context;
    let scale = 1;
    let topMarginPDFCoords = oneInch;
    let bottomMarginPDFCoords = oneInch;

  // https://stackoverflow.com/questions/7196212/how-to-create-dictionary-and-add-key-value-pairs-dynamically?rq=1
  // https://stackoverflow.com/questions/9251480/set-canvas-size-using-javascript/9251497
    
    let horizontalLineYHTMLCoords = [];
    // twoMins is used in the pdf case to store the vertical coordinates of the lines above and below the header row
    let twoMinsHTMLCoords = {};
    let headerLineList = [];
    let headerTextList = [];
    let currentPdfPage = 0;
    let maxPdfPage = 0;
    let pageDimensionsPDFCoords = {
      yMin: 0,
      yMax: Infinity
    }

    let verticalBreakPointsHTMLCoords = [];
    let paginatedData = [];

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
      if (flexibleToggle !== null) {
        document.getElementById(flexibleToggle).innerHTML = "Switch to Fixed View";
      }
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
      if (flexibleToggle !== null) {
        document.getElementById(flexibleToggle).innerHTML = "Switch to Flexible View";
      }
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

    //console.log('id: ', id);
    if (showPdfSchedule[id]) {
      //https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_toggle_hide_show
      //https://allyjs.io/tutorials/hiding-elements.html
      iframe.style.display = "block";
      canvas.style.display = "none";
      //console.log('showing iframe, but not canvas');
      stream = blobStream();
      context = new canvas2pdf.PdfContext(stream, {size: paperSize});
      //doc.addPage({size: 'A7'});

      // make the top margin a bit smaller if the schedule is long...it's still possible that the schedule will be
      // too long and will go off the bottom of the printed page, though.
      //if (height > this.maxHeight) {
      //  topMargin = oneInch;
      //  bottomMargin = oneInch;
      //} else {
      //  topMargin = oneInch;
      //  bottomMargin = oneInch;
      //}

      pageDimensionsPDFCoords = pageDimensionCalculator(oneInch, topMarginPDFCoords, bottomMarginPDFCoords, paperSize);
      
      console.log('page dimensions: ', pageDimensionsPDFCoords);

      for(var n = 0; n < line_list.length; n++) {
        if (isHorizontalLine(line_list[n])) {
          horizontalLineYHTMLCoords.push(line_list[n][1]);
        }
      }

      twoMinsHTMLCoords = minAndSecondMin(horizontalLineYHTMLCoords);
      console.log('mins: ', twoMinsHTMLCoords);

      //headerLineList = [];
      //lheaderTextList = [];

      for(var n = 0; n < line_list.length; n++) {
        if (isHeaderLine(line_list[n], twoMinsHTMLCoords)) {
          headerLineList.push(line_list[n]);
        }
      }

      console.log('header lines: ', headerLineList);

      for(var n = 0; n < table_text_list.length; n++) {
        if (isHeaderText(table_text_list[n], twoMinsHTMLCoords)) {
          headerTextList.push(table_text_list[n]);
        }
      }
      console.log('header text: ', headerTextList);

      iframe.width = width;
      iframe.height = height;
      scale = 0.61;


      console.log(horizontalLineYHTMLCoords);
      verticalBreakPointsHTMLCoords = verticalBreakPointCalculatorHTMLCoords(horizontalLineYHTMLCoords, twoMinsHTMLCoords, scale, pageDimensionsPDFCoords, currentPdfPage);

      console.log(verticalBreakPointsHTMLCoords);
      
      paginatedData = paginateData(line_list, filled_row_list, box_list, table_text_list, box_label_list, 
        headerTextList, headerLineList, scale, twoMinsHTMLCoords, verticalBreakPointsHTMLCoords, pageDimensionsPDFCoords);
      
      //console.log('height: ', height);
      
    } else {
      // the following is so we can keep the canvas and pdf code together...the canvas part will only have one "page"
      paginatedData = [
        {
          lineList: line_list,
          filledRowList: filled_row_list,
          boxList: box_list,
          tableTextList: table_text_list,
          boxLabelList: box_label_list
        }
      ];
      
      // https://allyjs.io/tutorials/hiding-elements.html
      iframe.style.display = "none";
      canvas.style.display = "block";
      //console.log('showing canvas, but not iframe');
      context = canvas.getContext('2d');
      // https://www.w3schools.com/TAGs/tryit.asp?filename=tryhtml5_canvas_height_width_clear
      canvas.width = width;
      canvas.height = height;
    }
    
    /*
    for(var n = 0; n < 11; n++) {
      context.beginPath();
      context.moveTo(10,72*n);
      context.lineTo(600,72*n);
      context.strokeStyle = 'red';
      context.stroke();
    }
    */

    for(var page = 0; page < paginatedData.length; page++) {

      let frl = paginatedData[page].filledRowList;
      let ll = paginatedData[page].lineList;
      let bl = paginatedData[page].boxList;
      let bll = paginatedData[page].boxLabelList;
      let ttl = paginatedData[page].tableTextList;
      let y1;
      let y2;

      for(var n = 0; n < frl.length; n++) {
        context.beginPath();
        //https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/rect
        context.rect(frl[n][0], frl[n][1], frl[n][2], frl[n][3]);
        context.fillStyle = frl[n][4];
        context.fill();
        context.lineWidth = frl[n][5];
        context.strokeStyle = frl[n][6];
        context.stroke();
        // From canvas2pdf docs: Calling fill and then stroke consecutively only executes fill;
        // to get around this, I'm constructing the rectangle a second time and only calling stroke the second time
        if (this.showPdfSchedule[id]) {
          context.beginPath();
        //https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/rect
          context.rect(frl[n][0], frl[n][1], frl[n][2], frl[n][3]);
          context.lineWidth = frl[n][5];
          context.strokeStyle = frl[n][6];
          context.stroke();
        }
      }
    
      for(var n = 0; n < ll.length; n++) {
        context.beginPath();
        context.moveTo(ll[n][0], ll[n][1]);
        context.lineTo(ll[n][2], ll[n][3]);
        context.lineWidth = grid_line_width;
        context.strokeStyle = grid_line_colour;
        context.lineCap = 'square';		
        context.stroke();
        }

      for(var n = 0; n < bl.length; n++) {
        context.beginPath();
        context.rect(bl[n][0], bl[n][1], bl[n][2], bl[n][3]);
        context.fillStyle = bl[n][4];
        context.fill();
        context.lineWidth = bl[n][5];
        context.strokeStyle = bl[n][6];
        context.stroke();
        // From canvas2pdf docs: Calling fill and then stroke consecutively only executes fill;
        // to get around this, I'm constructing the rectangle a second time and only calling stroke the second time
        // https://jenkov.com/tutorials/html5-canvas/stroke-fill.html
        if (this.showPdfSchedule[id]) {
          context.beginPath();
          context.rect(bl[n][0], bl[n][1], bl[n][2], bl[n][3]);
          context.lineWidth = bl[n][5];
          context.strokeStyle = bl[n][6];
          context.stroke();
        }
      }

      for(var n = 0; n < bll.length; n++) {
        context.textAlign = 'center';
        context.textBaseline = 'middle';		       
        context.fillStyle = bll[n][4];
        if (!this.showPdfSchedule[id]) {
          context.font = bll[n][3];
        } else {
          context.font = "bold 10pt Helvetica";
        }
        // console.log('font: ', bll[n][3]);
        // https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/fillText
        context.fillText(bll[n][2],bll[n][0],bll[n][1]);
      }
      
      for(var n = 0; n < ttl.length; n++) {
        context.textAlign = 'center';
        context.textBaseline = 'middle';		       
        context.fillStyle = ttl[n][4];
        //context.font = ttl[n][3];
        if (!this.showPdfSchedule[id]) {
          context.font = ttl[n][3];
        } else {
          context.font = "10pt Helvetica";
        }
        context.fillText(ttl[n][2],ttl[n][0],ttl[n][1]);
      }

      if (this.showPdfSchedule[id]) {
        context.addPage();
      }

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

  function isHorizontalLine(lineData) {
    // lines are in the form [x1, y1, x2, y2]; this returns true if y1 == y2, to within some tolerance
    let eps = 1;
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/abs
    return Math.abs(lineData[1]-lineData[3]) < eps;

  }

  function minAndSecondMin(yVals) {
    // takes in an array of yVals: [y1, y2, ..., yn] and returns the min and second min;
    // if two values are quite close, assumes them to be equal; the two mins must 
    // be separated by at least eps
    let eps = 1;
    let min = Infinity;
    let secondMin = Infinity;
    yVals.forEach( y => {
      if (y < min) {
        min = y;
      }
    });

    yVals.forEach( y => {
      if (y < secondMin && y - min > eps) {
        secondMin = y;
      }
    });

    return {
      min: min,
      secondMin: secondMin
    };
  }

  function isHeaderText(tableTextArray, twoMinsHTMLCoords) {
    // tableTextArray has elements like: [230.0, 70.0, 'Monday', '12pt Arial', '#2f2f2f'], which are of the form [x, y1,....];
    // this method compares the y coordinate to the data in the twoMins object and returns true if tableTextArray appears
    // to be a header row
    return  tableTextArray[1] > twoMinsHTMLCoords.min && tableTextArray[1] < twoMinsHTMLCoords.secondMin;
  }

  function isHeaderLine(lineData, twoMinsHTMLCoords) {
    // lineData has the form [x1, y1, x2, y2]; this function returns true if the line in question
    // appears to be a horizontal line that has coordinates consistent with either the min or the secondMin
    let eps = 1;
    //console.log(twoMinsHTMLCoords);
    return isHorizontalLine(lineData) && ((Math.abs(lineData[1] - twoMinsHTMLCoords.min) <= eps) || (Math.abs(lineData[1] - twoMinsHTMLCoords.secondMin) <= eps));
  }

  function pageDimensionCalculator(oneInch, topMargin, bottomMargin, paperSize) {
    // paperSize can be one of 'LETTER' or 'LEGAL'; topMargin and bottomMargin are assumed to be in PDF coordinates;
    // returns pageDimensions in PDF coordinates
    let length;
    length = paperSize === 'LETTER' ? 11*oneInch : 14*oneInch;
    return {
      yMin: topMargin,
      yMax: length - bottomMargin
    };
  }

  function pdfVerticalPositionCalculator(yValHTMLCoords, twoMinsHTMLCoords, scale, pageDimensionsPDFCoords, pageNumber) {
    // calculates the pdfVerticalPosition for a given yVal;
    // assumes that pages after the initial page have an extra header row displayed
    
  }

  function verticalBreakPointCalculatorHTMLCoords(horizontalLineYHTMLCoords, twoMinsHTMLCoords, scale, pageDimensionsPDFCoords, pageNumber) {
    let page = 0;
    let yValsByPageHTMLCoords = [];
    let yMin;
    let yMax;

    //https://medium.com/coding-at-dawn/how-to-sort-an-array-numerically-in-javascript-2b22710e3958
    horizontalLineYHTMLCoords.sort((a,b)=>a-b);
    console.log(horizontalLineYHTMLCoords);

    let yVal;
    let yNextVal;
    let firstValThisPage = true;
    let conditionLHS;
    let nMax = horizontalLineYHTMLCoords.length - 2;
    for(var n = 0; n < nMax + 1; n++) {
      yVal = horizontalLineYHTMLCoords[n];
      yNextVal = horizontalLineYHTMLCoords[n+1];
      console.log(n, yVal, yNextVal);
      if (n == 0) {
        yMin = yVal;
      }
      if (firstValThisPage) {
        yMax = yNextVal;
        console.log('first val this page', yMin, yMax);
        firstValThisPage = false;
      } 
      if (page == 0) {
        conditionLHS = yNextVal*scale + pageDimensionsPDFCoords.yMin
      } else {
        conditionLHS = (yNextVal-yMin)*scale + (twoMinsHTMLCoords.secondMin - twoMinsHTMLCoords.min)*scale + pageDimensionsPDFCoords.yMin;
      }
      if (conditionLHS <= pageDimensionsPDFCoords.yMax) {
        yMax = yNextVal;
        console.log('we are still within the page margin.... yMin, yMax: ', yMin, yMax);
        if (n == nMax) {
          yValsByPageHTMLCoords.push({
            page: page,
            yMinHTMLCoords: yMin,
            yMaxHTMLCoords: yMax
          });
        }
      } else {
        console.log('we wandered beyond the page margin.... yMin, yMax: ', yMin, yMax);
        yValsByPageHTMLCoords.push({
          page: page,
          yMinHTMLCoords: yMin,
          yMaxHTMLCoords: yMax
        });
        yMin = yMax;
        page += 1;
        firstValThisPage = true;
      }
    }

    return yValsByPageHTMLCoords;
      
      
     /* 
      else {
        console.log('we wandered beyond the page margin.... yMin, yMax: ', yMin, yMax);
        if (firstValThisPage) {
          // it's beyond the page margin, but we need to print it to this page anyway....
          yValsByPageHTMLCoords.push({
            page: page,
            yMinHTMLCoords: yMin,
            yMaxHTMLCoords: yMax
          });
        } 
      else {
        numValsThisPage += 1;
        console.log('NOT first val this page');
        if (page == 0) {
          conditionLHS = yNextVal*scale + pageDimensionsPDFCoords.yMin
        } else {
          conditionLHS = (yNextVal-yMaxPreviousPage)*scale + (twoMinsHTMLCoords.secondMin - twoMinsHTMLCoords.min)*scale + pageDimensionsPDFCoords.yMin;
        }
        if (conditionLHS <= pageDimensionsPDFCoords.yMax) {
          yMax = yNextVal;
          console.log('we are still within the page margin.... yMax: ', yMax);
        } else {
          console.log('we wandered beyond the page margin.... yMin, yMax: ', yMin, yMax);
          if ()
          yValsByPageHTMLCoords.push({
            page: page,
            yMinHTMLCoords: yMin,
            yMaxHTMLCoords: yMax
          });
          yMaxPreviousPage = yNextVal;
          page += 1;
          firstValThisPage = true;
        }
      }
    }
    if (!firstValThisPage) {
      // push the last yMin and yMax values, since those didn't get added to the array yet
      yValsByPageHTMLCoords.push({
        page: page,
        yMinHTMLCoords: yMin,
        yMaxHTMLCoords: yMax
      });
    }
    console.log(yValsByPageHTMLCoords);

    /*
      if (page == 0) {
        if (yVal*scale + pageDimensionsPDFCoords.yMin <= pageDimensionsPDFCoords.yMax) {
          if (yValHTMLCoords < yMin) {
            yMin = yValHTMLCoords;
          }
          if (yValHTMLCoords > yMax) {
            yMax = yValHTMLCoords;
          }
        }
      } else {
        if ((yValHTMLCoords-yMaxPreviousPage)*scale + (twoMinsHTMLCoords.secondMin - twoMinsHTMLCoords.min)*scale + pageDimensionsPDFCoords.yMin <= pageDimensionsPDFCoords.yMax) {
          if (yValHTMLCoords > yMax) {
            yMax = yValHTMLCoords;
          }
        }
      }
    }


    horizontalLineYHTMLCoords.forEach( yValHTMLCoords => { 

    });



    // What if one block is so large that it simply cannot fit on a page?!? currently the routine is just truncating in that case, which isn't good...!
    while (page < 10 & (!maxPageReached)) {
      horizontalLineYHTMLCoords.forEach( yValHTMLCoords => { 
        if (page == 0) {
          if (yValHTMLCoords*scale + pageDimensionsPDFCoords.yMin <= pageDimensionsPDFCoords.yMax) {
            if (yValHTMLCoords < yMin) {
              yMin = yValHTMLCoords;
            }
            if (yValHTMLCoords > yMax) {
              yMax = yValHTMLCoords;
            }
          }
        } else {
          if ((yValHTMLCoords-yMaxPreviousPage)*scale + (twoMinsHTMLCoords.secondMin - twoMinsHTMLCoords.min)*scale + pageDimensionsPDFCoords.yMin <= pageDimensionsPDFCoords.yMax) {
            if (yValHTMLCoords > yMax) {
              yMax = yValHTMLCoords;
            }
          }
        }
      });
      if (approximatelyEqual(yMin, yMax)) {
        maxPageReached = true;
      } else {
        yValsByPageHTMLCoords.push({
          page: page,
          yMinHTMLCoords: yMin,
          yMaxHTMLCoords: yMax
        });
      }
      yMaxPreviousPage = yMax;
      yMin = yMax; // yMin for the next page is yMax from the previous page, since we're going to need to draw this line again
      yMax = -Infinity;
      page += 1;
    }
    */
    

  }

  function paginateData(line_list, filled_row_list, box_list, table_text_list, box_label_list, headerTextList, headerLineList, scale, twoMinsHTMLCoords, verticalBreakPointsHTMLCoords, pageDimensionsPDFCoords) {
    
    let paginatedData = [];
    let pageObject;
    let pageObjects = [];
    for(var page=0; page < verticalBreakPointsHTMLCoords.length; page++) {
      paginatedData.push({
        lineList: [],
        filledRowList: [],
        boxList: [],
        tableTextList: [],
        boxLabelList: []
      });
    }

    box_list.forEach(box => {
      pageObject = boxPageCalculator(box, verticalBreakPointsHTMLCoords);
      //console.log(pageObject);
      //console.log(pageObject.page, typeof pageObject.page);
      //console.log('paginated data, this page:', paginatedData[pageObject.page]);
      let yVal = yValCalculator(box[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
      paginatedData[pageObject.page].boxList.push([scale*box[0], yVal, scale*box[2], scale*box[3], box[4], box[5], box[6]]);
    });

    filled_row_list.forEach(box => {
      pageObject = boxPageCalculator(box, verticalBreakPointsHTMLCoords);
      //console.log(pageObject);
      //console.log(pageObject.page, typeof pageObject.page);
      //console.log('paginated data, this page:', paginatedData[pageObject.page]);
      let yVal = yValCalculator(box[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
      paginatedData[pageObject.page].filledRowList.push([scale*box[0], yVal, scale*box[2], scale*box[3], box[4], box[5], box[6]]);
    });

    // add header text to all pages after the first one
    for(var page = 1; page < verticalBreakPointsHTMLCoords.length; page++) {
      console.log('PAGE!', page);
      pageObject = verticalBreakPointsHTMLCoords[page];
      console.log(pageObject);
      console.log(pageObject.page, typeof pageObject.page);
      console.log('paginated data, this page:', paginatedData[pageObject.page]);
      headerTextList.forEach(text => {
        let yVal = scale*text[1] + pageDimensionsPDFCoords.yMin
        console.log([scale*text[0], yVal, text[2], text[3], text[4]]);
        paginatedData[page].tableTextList.push([scale*text[0], yVal, text[2], text[3], text[4]]);
      });
    }
    
    table_text_list.forEach(text => {
      //console.log(text);
      pageObject = boxPageCalculator(text, verticalBreakPointsHTMLCoords);
      //console.log(pageObject);
      //console.log(pageObject.page, typeof pageObject.page);
      //console.log('paginated data, this page:', paginatedData[pageObject.page]);
      let yVal = yValCalculator(text[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
      paginatedData[pageObject.page].tableTextList.push([scale*text[0], yVal, text[2], text[3], text[4]]);
    });

    box_label_list.forEach(text => {
      //console.log(text);
      pageObject = boxPageCalculator(text, verticalBreakPointsHTMLCoords);
      //console.log(pageObject);
      //console.log(pageObject.page, typeof pageObject.page);
      //console.log('paginated data, this page:', paginatedData[pageObject.page]);
      let yVal = yValCalculator(text[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
      paginatedData[pageObject.page].boxLabelList.push([scale*text[0], yVal, text[2], text[3], text[4]]);
    });

    /*
    line_list.forEach(line => {
      //console.log(text);
      if (isHorizontalLine(line)) {
        pageObjects = linePageCalculator(line, verticalBreakPointsHTMLCoords);
        [ could be one or two ]


        WORKING HERE

      }
      
      //console.log(pageObject);
      //console.log(pageObject.page, typeof pageObject.page);
      //console.log('paginated data, this page:', paginatedData[pageObject.page]);
      let yVal = yValCalculator(text[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
      paginatedData[pageObject.page].boxLabelList.push([scale*text[0], yVal, text[2], text[3], text[4]]);
    });
    */
    return paginatedData;
  }


  

  function boxPageCalculator(boxData, verticalBreakPointsHTMLCoords) {
    let pageObjectThisBox = {};
    let numSolns = 0;
    let eps = 1;
    if (verticalBreakPointsHTMLCoords.length > 0) {
      // there is one case where coordinates do not fall within the "usual" range dictated by the 
      // the horizontal lines in the table, and that is the title that should go at the top of the first page
      pageObjectThisBox = verticalBreakPointsHTMLCoords[0];
    }
    verticalBreakPointsHTMLCoords.forEach(pageObj => {

      //if (approximatelyEqual(boxData[1], pageObj.yMaxHTMLCoords) || approximatelyEqual(boxData[1], pageObj.yMinHTMLCoords)) {
      //  console.log('box is close to the boundary!', boxData[1], pageObj);
      //}

      if ((boxData[1] < pageObj.yMaxHTMLCoords - eps) && (boxData[1] >= pageObj.yMinHTMLCoords - eps)) {

        pageObjectThisBox = pageObj;
        //console.log('seletected page object: ', pageObj);
        
        numSolns += 1;
      }
    });
    console.log('numSolns: ', numSolns);
    return pageObjectThisBox;
  }

  function linePageCalculator(horizontalLineData, verticalBreakPointsHTMLCoords) {
    let pageObjectsThisLine = []; // if a horizontal line is at the end of a page, it should also show up at the beginning of the next
    
    verticalBreakPointsHTMLCoords.forEach(pageObj => {
      if (lessThanApprox(horizontalLineData[1], pageObj.yMaxHTMLCoords) && greaterThanApprox(horizontalLineData[1], pageObj.yMinHTMLCoords)) {
        pageObjectsThisLine.push(pageObj);   
      }
    });
    return pageObjectsThisLine;
  }



  function approximatelyEqual(val1, val2) {
    let eps = 1;
    return Math.abs(val1-val2) <= eps;
  }

  /*
  function lessThanApprox(val1, val2) {
    let eps = 1;
    return val1 <= val2 + eps;
  }

  function greaterThanApprox(val1, val2) {
    let eps = 1;
    return val1 >= val2 - eps;
  }
  */

  function yValCalculator(yHTML, pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords) {
    return pageObject.page == 0 ? scale*yHTML + pageDimensionsPDFCoords.yMin : scale*(yHTML-pageObject.yMinHTMLCoords) + (twoMinsHTMLCoords.secondMin - twoMinsHTMLCoords.min)*scale + pageDimensionsPDFCoords.yMin;
  }