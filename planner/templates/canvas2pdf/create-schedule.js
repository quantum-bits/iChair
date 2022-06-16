function createSchedule(id, flexibleScheduleToggle, pdfScheduleToggle, paperSize = 'LETTER', 
    scheduleData, showFlexibleSchedule, showPdfSchedule, htmlElementIds = {}) {
  
    flexibleToggle = htmlElementIds.toggle === null ? null : htmlElementIds.toggle+id;
    spanSwitchToPdf = htmlElementIds.pdf+id;
    spanSwitchToNormal = htmlElementIds.normal+id;
    spanSwitchToLegal =  htmlElementIds.legal+id;
    spanSwitchToLetter = htmlElementIds.letter+id;
    
    if (flexibleScheduleToggle) {
        showFlexibleSchedule[id] = !showFlexibleSchedule[id];
    }
    if (pdfScheduleToggle) {
        showPdfSchedule[id] = !showPdfSchedule[id];
    }

    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Default_parameters

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
    }

    if (showPdfSchedule[id]) {
      //https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_toggle_hide_show
      //https://allyjs.io/tutorials/hiding-elements.html
      iframe.style.display = "block";
      canvas.style.display = "none";
      stream = blobStream();
      context = new canvas2pdf.PdfContext(stream, {size: paperSize});

      pageDimensionsPDFCoords = pageDimensionCalculator(oneInch, topMarginPDFCoords, bottomMarginPDFCoords, paperSize);
      
      for(var n = 0; n < line_list.length; n++) {
        if (isHorizontalLine(line_list[n])) {
          horizontalLineYHTMLCoords.push(line_list[n][1]);
        }
      }

      twoMinsHTMLCoords = minAndSecondMin(horizontalLineYHTMLCoords);
     
      for(var n = 0; n < line_list.length; n++) {
        if (isHeaderLine(line_list[n], twoMinsHTMLCoords)) {
          headerLineList.push(line_list[n]);
        }
      }

      for(var n = 0; n < table_text_list.length; n++) {
        if (isHeaderText(table_text_list[n], twoMinsHTMLCoords)) {
          headerTextList.push(table_text_list[n]);
        }
      }

      iframe.width = Math.min(width, 850);
      iframe.height = Math.min(height, 800);
      scale = 0.61;

      verticalBreakPointsHTMLCoords = verticalBreakPointCalculatorHTMLCoords(horizontalLineYHTMLCoords, twoMinsHTMLCoords, scale, pageDimensionsPDFCoords, currentPdfPage);
      
      paginatedData = paginateData(line_list, filled_row_list, box_list, table_text_list, box_label_list, 
        headerTextList, headerLineList, scale, twoMinsHTMLCoords, verticalBreakPointsHTMLCoords, pageDimensionsPDFCoords);
            
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
      context = canvas.getContext('2d');
      // https://www.w3schools.com/TAGs/tryit.asp?filename=tryhtml5_canvas_height_width_clear
      canvas.width = width;
      canvas.height = height;
    }
    
    for(var page = 0; page < paginatedData.length; page++) {

      if (this.showPdfSchedule[id] && page > 0) {
        context.addPage();
      }

      let frl = paginatedData[page].filledRowList;
      let ll = paginatedData[page].lineList;
      let bl = paginatedData[page].boxList;
      let bll = paginatedData[page].boxLabelList;
      let ttl = paginatedData[page].tableTextList;

      /*
      // uncomment the following to show the top and bottom margins
      if (showPdfSchedule[id]) {
        context.beginPath();
        context.moveTo(10,pageDimensionsPDFCoords.yMin);
        context.lineTo(600,pageDimensionsPDFCoords.yMin);
        context.strokeStyle = 'red';
        context.stroke();
        context.beginPath();
        context.moveTo(10,pageDimensionsPDFCoords.yMax);
        context.lineTo(600,pageDimensionsPDFCoords.yMax);
        context.strokeStyle = 'red';
        context.stroke();
      }
      */

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

    }

    if (showPdfSchedule[id]) {
      context.end();
      context.stream.on('finish', function () {
        iframe.src = context.stream.toBlobURL('application/pdf');
        // not sure what the following does....
        //var blob = ctx.stream.toBlob('application/pdf');
        //saveAs(blob, 'example.pdf', true);
        // https://stackoverflow.com/questions/3569329/javascript-to-make-the-page-jump-to-a-specific-location
        document.getElementById("schedule-"+id).scrollIntoView({behavior: 'smooth'});
      });
    }
  }

  function isHorizontalLine(lineData) {
    // lines are in the form [x1, y1, x2, y2]; this returns true if y1 == y2, to within some tolerance
    let eps = 1;
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/abs
    return Math.abs(lineData[1]-lineData[3]) < eps;
  }

  function isVerticalLine(lineData) {
    // lines are in the form [x1, y1, x2, y2]; this returns true if x1 == x2, to within some tolerance
    let eps = 1;
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/abs
    return Math.abs(lineData[0]-lineData[0]) < eps;

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

    let yVal;
    let yNextVal;
    let conditionLHS;
    let nMax = horizontalLineYHTMLCoords.length - 2;
    let numDataRowsThisPage = 0;
    for(var n = 0; n < nMax + 1; n++) {
      yVal = horizontalLineYHTMLCoords[n];
      yNextVal = horizontalLineYHTMLCoords[n+1];
      if (n == 0) {
        yMin = yVal;
      }
      if (page == 0) {
        conditionLHS = yNextVal*scale + pageDimensionsPDFCoords.yMin
      } else {
        conditionLHS = (yNextVal-yMin)*scale + (twoMinsHTMLCoords.secondMin - twoMinsHTMLCoords.min)*scale + pageDimensionsPDFCoords.yMin;
      }
      if (conditionLHS > pageDimensionsPDFCoords.yMax) {
        // the next value oversteps the boundary
        if (numDataRowsThisPage >= 1) {
          // if we have at least one row of data on this page, then we can move on to the next page
          yValsByPageHTMLCoords.push({
            page: page,
            yMinHTMLCoords: yMin,
            yMaxHTMLCoords: yMax
          });
          yMin = yMax;
          yMax = yNextVal;
          page += 1;
          numDataRowsThisPage = 1; // the next page will automatically get the one that overstepped the boundary....
          if (n == nMax) {
            yValsByPageHTMLCoords.push({
              page: page,
              yMinHTMLCoords: yMin,
              yMaxHTMLCoords: yMax
            });
          }
        } else {
          // we're beyond the margin, but we don't yet have one row of data
          yMax = yNextVal;
          if (n > 0) {
            // if n == 0, the current row is the header row, so that doesn't count as a row of data
            numDataRowsThisPage += 1;
          }
        }
      } else {
        yMax = yNextVal;
        if (n > 0) {
          // if n == 0, the current row is the header row, so that doesn't count as a row of data
          numDataRowsThisPage += 1;
        }
        if (n == nMax) {
          yValsByPageHTMLCoords.push({
            page: page,
            yMinHTMLCoords: yMin,
            yMaxHTMLCoords: yMax
          });
        }
      }
    }    
    return yValsByPageHTMLCoords;
  }

  function paginateData(line_list, filled_row_list, box_list, table_text_list, box_label_list, headerTextList, headerLineList, scale, twoMinsHTMLCoords, verticalBreakPointsHTMLCoords, pageDimensionsPDFCoords) {
    
    let paginatedData = [];
    let pageObject;
    let pageObjects = [];
    let yMinHTMLCoords = determineYMinYMaxHTMLCoords(verticalBreakPointsHTMLCoords).yMin;
    let yMaxHTMLCoords = determineYMinYMaxHTMLCoords(verticalBreakPointsHTMLCoords).yMax;

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
      let yVal = yValCalculator(box[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
      paginatedData[pageObject.page].boxList.push([scale*box[0], yVal, scale*box[2], scale*box[3], box[4], box[5], box[6]]);
    });

    filled_row_list.forEach(box => {
      pageObject = boxPageCalculator(box, verticalBreakPointsHTMLCoords);
      let yVal = yValCalculator(box[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
      paginatedData[pageObject.page].filledRowList.push([scale*box[0], yVal, scale*box[2], scale*box[3], box[4], box[5], box[6]]);
    });

    // add header text to all pages after the first one
    for(var page = 1; page < verticalBreakPointsHTMLCoords.length; page++) {
      pageObject = verticalBreakPointsHTMLCoords[page];
      headerTextList.forEach(text => {
        // centering the header text manually....
        let yVal = 0.5*(twoMinsHTMLCoords.secondMin - twoMinsHTMLCoords.min)*scale + pageDimensionsPDFCoords.yMin;
        paginatedData[page].tableTextList.push([scale*text[0], yVal, text[2], text[3], text[4]]);
      });
    }

    // add horizontal line above header row for pages after the first one
    if (headerLineList.length > 0) {
      let line = headerLineList[0];
      let yVal = pageDimensionsPDFCoords.yMin;
      for(var page = 1; page < verticalBreakPointsHTMLCoords.length; page++) {
        paginatedData[page].lineList.push([scale*line[0], yVal, scale*line[2], yVal]);
      }
    }
    
    table_text_list.forEach(text => {
      pageObject = boxPageCalculator(text, verticalBreakPointsHTMLCoords);
      let yVal = yValCalculator(text[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
      paginatedData[pageObject.page].tableTextList.push([scale*text[0], yVal, text[2], text[3], text[4]]);
    });

    box_label_list.forEach(text => {
      pageObject = boxPageCalculator(text, verticalBreakPointsHTMLCoords);
      let yVal = yValCalculator(text[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
      paginatedData[pageObject.page].boxLabelList.push([scale*text[0], yVal, text[2], text[3], text[4]]);
    });


    line_list.forEach(line => {
      if (isHorizontalLine(line)) {
        // one line could show up at the end of one page and the beginning of the next
        pageObjects = horizontalLinePageCalculator(line, verticalBreakPointsHTMLCoords);
        pageObjects.forEach(pageObject => {
          let yVal = yValCalculator(line[1], pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
          paginatedData[pageObject.page].lineList.push([scale*line[0], yVal, scale*line[2], yVal]);
        });
      } else if (isVerticalLine(line)) {
        // most (all?) vertical lines should go from the very top to the very bottom of the table;
        // check this first; if so, just add the lines to each page as appropriate
        if ((approximatelyEqual(line[1], yMinHTMLCoords) && approximatelyEqual(line[3], yMaxHTMLCoords)) || (approximatelyEqual(line[3], yMinHTMLCoords) && approximatelyEqual(line[1], yMaxHTMLCoords))) {
          // write line to list
          for(var page = 0; page < verticalBreakPointsHTMLCoords.length; page++) {
            if (page == 0) {
              let yMinValPDFCoords = yValCalculator(verticalBreakPointsHTMLCoords[page].yMinHTMLCoords, verticalBreakPointsHTMLCoords[page], scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
              let yMaxValPDFCoords = scale*verticalBreakPointsHTMLCoords[page].yMaxHTMLCoords + pageDimensionsPDFCoords.yMin;
              paginatedData[page].lineList.push([scale*line[0], yMinValPDFCoords, scale*line[2], yMaxValPDFCoords]);
            } else {
              let yMaxValPDFCoords = yValCalculator(verticalBreakPointsHTMLCoords[page].yMaxHTMLCoords, verticalBreakPointsHTMLCoords[page], scale, pageDimensionsPDFCoords, twoMinsHTMLCoords);
              paginatedData[page].lineList.push([scale*line[0], pageDimensionsPDFCoords.yMin, scale*line[2], yMaxValPDFCoords]);
            }
          }
        } else {
          console.log('The line does not seem to go from the top of the table to the bottom!');
          console.log('line: ',line);
          console.log('yMinHTMLCoords: ', yMinHTMLCoords);
          console.log('yMaxHTMLCoords: ', yMaxHTMLCoords);
        }
      } else {
        console.log('The line does not appear to be horizontal or vertical!');
      }
    });

    return paginatedData;
  }

  function determineYMinYMaxHTMLCoords(verticalBreakPointsHTMLCoords) {
    let yMin=Infinity;
    let yMax=-Infinity;
    verticalBreakPointsHTMLCoords.forEach(breakPoint => {
      if (breakPoint.yMinHTMLCoords < yMin) {
        yMin = breakPoint.yMinHTMLCoords;
      }
      if (breakPoint.yMaxHTMLCoords > yMax) {
        yMax = breakPoint.yMaxHTMLCoords;
      }
    });
    return {yMin: yMin, yMax: yMax};
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
      if ((boxData[1] < pageObj.yMaxHTMLCoords - eps) && (boxData[1] >= pageObj.yMinHTMLCoords - eps)) {
        pageObjectThisBox = pageObj;
        numSolns += 1;
      }
    });
    if (numSolns > 1) {
      console.log('Warning!!!  numSolns is greater than 1: ', numSolns);
    }
    return pageObjectThisBox;
  }

  function horizontalLinePageCalculator(horizontalLineData, verticalBreakPointsHTMLCoords) {
    let pageObjectsThisLine = []; // if a horizontal line is at the end of a page, it should also show up at the beginning of the next
    let numSolns = 0;
    let eps = 1;
    verticalBreakPointsHTMLCoords.forEach(pageObj => {
      if ((horizontalLineData[1] <= pageObj.yMaxHTMLCoords + eps) && (horizontalLineData[1] >= pageObj.yMinHTMLCoords - eps)) {
        pageObjectsThisLine.push(pageObj);   
        numSolns += 1;
      }
    });
    return pageObjectsThisLine;
  }

  function approximatelyEqual(val1, val2) {
    let eps = 1;
    return Math.abs(val1-val2) <= eps;
  }

  function yValCalculator(yHTML, pageObject, scale, pageDimensionsPDFCoords, twoMinsHTMLCoords) {
    return pageObject.page == 0 ? scale*yHTML + pageDimensionsPDFCoords.yMin : scale*(yHTML-pageObject.yMinHTMLCoords) + (twoMinsHTMLCoords.secondMin - twoMinsHTMLCoords.min)*scale + pageDimensionsPDFCoords.yMin;
  }