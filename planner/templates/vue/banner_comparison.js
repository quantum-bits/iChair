// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const
const CREATE_NEW_COURSE = -2;
const DO_NOTHING = -1;

var app = new Vue({
  delimiters: ["[[", "]]"],
  el: "#app",
  vuetify: new Vuetify(),
  data() {
    return {
        semesterFractionsReverse: {}, // used to convert 
        semesterFractions: {},
      choosingSemesters: true, // set to false once semesters have been chosen to work on
      semesterChoices: [], // filled in via an ajax request after the component is mounted
      chosenSemesters: [], // ids of semesters chosen to work on
      //aligningCourses: false, // set to true once we start aligning courses (if necessary)
      courseAlignmentPhaseReady: false,
      //courseAlignmentChoices: [], // used to populate radio select elements in the table used for aligning courses
      unmatchedCourses: [], // filled in via an ajax request after one or more semesters are chosen; also used to populate radio select elements in the table used for aligning courses
      displayCreateUpdateErrorMessage: false,
      expanded: [],
      singleExpand: true,
      message: "Hello Vue!",
      search: "",
      json_data: json_data,
      page: 1,
      pageCount: 0,
      itemsPerPage: 15,
      showAllCourses: false,
      buttonRipple: false,
      headers: [
        { text: "Semester", value: "semester" },
        { text: "CRN", value: "crn" },
        {
          text: "Number",
          align: "left",
          sortable: true,
          value: "number"
        },
        { text: "Name", value: "name", align: "left" },
        { text: "Status", value: "status", align: "center" }
      ],
      courseOfferingAlignmentPhaseReady: false, // set to true once we're ready to start comparing course offerings
      courseOfferings: [],
      dialog: false, // true when the dialog is being displayed
      dialogTitle: "",
      editMeetings: [], // used to store the data in the class schedule form
      editCourseOfferingData: {}, // used to store some data that can be used upon submitting the class schedule form
      initialMeetingData: [], // used to hold on to the initial class schedule (before editing)
      meetingFormErrorMessage: "", // used to display errors in the class scheduling form
      pagination: {
        rowsPerPage: 20
      }
    };
  },
  methods: {
    alignCourses() {
      // second step of the process...so we turn off the 'select semesters' template
      console.log('inside align courses');
      var _this = this;
      this.choosingSemesters = false;
      $.ajax({
        // initialize an AJAX request
        type: "GET",
        url: "/planner/ajax/fetch-courses-to-be-aligned/", // set the url of the request
        dataType: "json",
        data: {
          departmentId: json_data.departmentId, // add the department id to the GET parameters
          yearId: json_data.yearId
        },
        success: function(incomingData) {
          console.log(incomingData);
            //this.unmatchedCourses = incomingData.unmatched_courses;
            console.log(incomingData.unmatched_courses);
            _this.unmatchedCourses = [];
            let unmatchedCourse = null;
            let choices = null;
            let num_offerings = '';
            let max_num_offerings = 0;
            let credit_text = '';
            /**
             * course.choice = -1 ==> do nothing
             * course.choice = -2 ==> create new course
             * course.choice = iChair course id ==> set banner_title in iChair course to banner title (in data warehouse database)
             */
            incomingData.unmatched_courses.forEach( course => {
                unmatchedCourse = course;
                choices = [];
                if (course.ichair_courses.length === 0) {
                    unmatchedCourse.choice = CREATE_NEW_COURSE; // default is to create a new course
                    choices.push({
                        bannerCourseId: course.banner_course.id,
                        selectionId: CREATE_NEW_COURSE,//assuming actual db ids will never be negative
                        text: "Create a new matching course (recommended, since there is currently no matching course in iChair)"
                    })
                } else {
                    max_num_offerings = 0;
                    unmatchedCourse.choice = DO_NOTHING; // default starts as "do nothing"
                    course.ichair_courses.forEach( item => {
                        if (item.number_offerings_this_year > max_num_offerings) {
                            max_num_offerings = item.number_offerings_this_year;
                            unmatchedCourse.choice = item.id; // default becomes to choose the course with the greatest # of course offerings
                        }
                        if (item.credit_hours == 1) {
                            credit_text = ' credit hour; ';
                        } else {
                            credit_text = ' credit hours; ';
                        }
                        item.number_offerings_this_year == 1 ? num_offerings = ' offering ' : num_offerings = ' offerings ';
                        choices.push({
                            bannerCourseId: course.banner_course.id,
                            selectionId: item.id,//assuming actual db ids will never be negative
                            text: item.subject+' '+item.number+': '+item.title+' ('+item.credit_hours+credit_text+
                                item.number_offerings_this_year+num_offerings+'this year)'
                        })
                    });
                    choices.push({
                        bannerCourseId: course.banner_course.id,
                        selectionId: CREATE_NEW_COURSE,//assuming actual db ids will never be negative
                        text: "Create a new matching course (not recommended in this case)"
                    })
                }
                choices.push({
                    bannerCourseId: course.banner_course.id,
                    selectionId: DO_NOTHING,//assuming actual db ids will never be negative
                    text: "Do nothing for now...."
                });
                unmatchedCourse.choices = choices;
                _this.unmatchedCourses.push(unmatchedCourse);
        });
        //_this.unmatchedCourses = cAC;
        console.log(_this.unmatchedCourses);
        _this.courseAlignmentPhaseReady = true;
        console.log(_this.courseAlignmentPhaseReady);
        }
      });
  
    },
    performCourseAlignment() {
        console.log(this.unmatchedCourses);
        var _this = this;
        let dataForPost = {
            create: [],
            update: []
        };
        this.unmatchedCourses.forEach( course => {
            if (course.choice == CREATE_NEW_COURSE) {
                dataForPost.create.push({
                    title: course.banner_course.title,
                    credit_hours: course.banner_course.credit_hours,
                    number: course.banner_course.number,
                    subject_id: course.ichair_subject_id
                })
            } else if (course.choice == DO_NOTHING) {
                console.log('do nothing: ', course.banner_course.title);
            } else {
                dataForPost.update.push({
                    ichair_course_id: course.choice,
                    banner_title: course.banner_course.title
                })
            }
        });
        if ((dataForPost.create.length == 0) && (dataForPost.update.length == 0)) {
            //nothing to do; move on to the next step....
            this.alignCourseOfferings();
        }
        $.ajax({
            // initialize an AJAX request
            type: "POST",
            url: "/planner/ajax/create-update-courses/",
            dataType: "json",
            data: JSON.stringify(dataForPost),
            success: function(jsonResponse) {
                console.log('response: ', jsonResponse);
                if (!(jsonResponse.updates_successful && jsonResponse.creates_successful)) {
                    _this.showCreateUpdateErrorMessage();
                } else {
                    _this.alignCourseOfferings();
                }
            },
            error: function(jqXHR, exception) {
              // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
              console.log(jqXHR);
              _this.showCreateUpdateErrorMessage();
              //_this.meetingFormErrorMessage =
              //  "Sorry, there appears to have been an error.";
            }
          });


    },
    showCreateUpdateErrorMessage() {
        this.displayCreateUpdateErrorMessage = true;
        this.courseAlignmentPhaseReady = false;
    },
    alignCourseOfferings() {
        this.courseAlignmentPhaseReady = false;
        this.displayCreateUpdateErrorMessage = false;
        console.log('align course offerings!');
        var _this = this;

        let dataForPost = {
            departmentId: json_data.departmentId, // add the faculty id to the GET parameters
            yearId: json_data.yearId,
            semesterIds: this.chosenSemesters
        }

        $.ajax({
            // initialize an AJAX request
            // seems like this should be a GET request, but I'm having trouble sending along the json data that way....
            type: "POST",
            url: "/planner/ajax/fetch-banner-comparison-data/", // set the url of the request
            dataType: "json",
            data: JSON.stringify(dataForPost),
            success: function(incomingData) {
              // https://stackoverflow.com/questions/3590685/accessing-this-from-within-an-objects-inline-function
              incomingData.course_data.forEach(course => {
                _this.courseOfferings.push({
                  semester: course.semester,
                  number: course.course,
                  name: course.course_title,
                  crn: course.crn,
                  schedulesMatch: course.schedules_match,
                  instructorsMatch: course.instructors_match,
                  semesterFractionsMatch: course.semester_fractions_match,
                  ichair: course.ichair,
                  banner: course.banner,
                  hasIChair: course.has_ichair,
                  hasBanner: course.has_banner,
                  linked: course.linked,
                  allOK: course.all_OK
                });
                console.log(course.ichair.semester_fraction);
                console.log(typeof(course.ichair.semester_fraction));
              });
              _this.semesterFractionsReverse = incomingData.semester_fractions_reverse;
              _this.semesterFractions = incomingData.semester_fractions;
              _this.courseOfferingAlignmentPhaseReady = true;
              console.log('course offering data: ', _this.courseOfferings);
              console.log('sem fractions: ', _this.semesterFractions);
              console.log(typeof(_this.semesterFractions.full))
            }
          });




    },

    showAll() {
      this.itemsPerPage = this.courseOfferings.length;
      this.page = 1;
      this.showAllCourses = true;
    },
    showFewer() {
      this.itemsPerPage = 15;
      this.showAllCourses = false;
    },
    editMeetingTimes(courseInfo) {
      this.editCourseOfferingData = {
        courseOfferingId: courseInfo.ichair.course_offering_id,
        ichairObject: courseInfo.ichair
      };
      this.dialogTitle = courseInfo.number + ": " + courseInfo.name;
      let meetingDetails = courseInfo.ichair.meeting_times_detail;
      this.dialog = true;
      //trick to clone the object: https://www.codementor.io/junedlanja/copy-javascript-object-right-way-ohppc777d
      this.editMeetings = JSON.parse(JSON.stringify(meetingDetails));
      this.editMeetings.forEach(meeting => {
        meeting.delete = false;
      });
      this.initialMeetingData = meetingDetails;
      this.addMeetingTime();
      this.addMeetingTime();
    },
    editSemesterFraction(courseInfo) {
        console.log('edit semester fraction!');
    },
    addNewMeetingTimes(courseInfo) {
      console.log(courseInfo);
    },
    addMeetingTime() {
      this.editMeetings.push({
        delete: false,
        day: 0,
        begin_at: "",
        end_at: "",
        id: null
      });
    },
    cancelMeetingsForm() {
      this.dialog = false;
      this.editMeetings = [];
      this.meetingFormErrorMessage = "";
      this.editCourseOfferingData = {};
    },
    submitMeetingsForm() {
      let meetingsToDelete = []; //list of ids
      let meetingsToUpdate = []; //list of objects
      let meetingsToCreate = []; //list of objects
      let meetingsToLeave = []; //list of objects
      this.meetingFormErrorMessage = "";
      let formOK = true;
      this.editMeetings.forEach(meeting => {
        if (meeting.id !== null && meeting.delete === true) {
          meetingsToDelete.push(meeting.id);
        } else if (meeting.delete === false) {
          // check if need to make updates....
          if (meeting.begin_at !== "" || meeting.end_at !== "") {
            if (meeting.id === null) {
              let checkTime = this.checkTimes(meeting.begin_at, meeting.end_at);
              if (checkTime.timesOK) {
                meetingsToCreate.push({
                  day: parseInt(meeting.day),
                  begin_at: meeting.begin_at,
                  end_at: meeting.end_at
                });
              } else {
                this.meetingFormErrorMessage = checkTime.errorMessage;
                formOK = false;
              }
            } else {
              let checkTime = this.checkTimes(meeting.begin_at, meeting.end_at);
              // now check if anything is different....
              let timesIdentical = true;
              if (!checkTime.timesOK) {
                this.meetingFormErrorMessage = checkTime.errorMessage;
                formOK = false;
              } else {
                // now check if anything has been changed in the form;
                // find the corresponding element in this.initialMeetingData and look for differences....
                let foundMeeting = false;
                let matchingMeeting = null;
                this.initialMeetingData.forEach(initialData => {
                  if (initialData.id === meeting.id) {
                    foundMeeting = true;
                    matchingMeeting = initialData;
                  }
                });
                if (foundMeeting) {
                  // meeting.day could come from the form, so it might be a string....
                  timesIdentical =
                    matchingMeeting.day === parseInt(meeting.day) &&
                    matchingMeeting.begin_at === meeting.begin_at &&
                    matchingMeeting.end_at === meeting.end_at;
                } else {
                  console.log(
                    "something is wrong! cannot find the id for the update...."
                  );
                }
                if (!timesIdentical) {
                  meetingsToUpdate.push({
                    id: meeting.id,
                    day: parseInt(meeting.day),
                    begin_at: meeting.begin_at,
                    end_at: meeting.end_at
                  });
                } else {
                  meetingsToLeave.push({
                    id: meeting.id,
                    day: parseInt(meeting.day),
                    begin_at: meeting.begin_at,
                    end_at: meeting.end_at
                  });
                }
              }
            }
          }
        }
      });
      let meetingSummary = [];
      meetingsToCreate.forEach(meeting => meetingSummary.push(meeting));
      meetingsToUpdate.forEach(meeting => meetingSummary.push(meeting));
      meetingsToLeave.forEach(meeting => meetingSummary.push(meeting));
      if (formOK) {
        // everything else is OK, so check if the various times conflict with each other
        let checkTimeOverlaps = this.checkTimeConflicts(meetingSummary);
        if (!checkTimeOverlaps.timesOK) {
          this.meetingFormErrorMessage = checkTimeOverlaps.errorMessage;
          formOK = false;
        }
      }
      let numChanges =
        meetingsToCreate.length +
        meetingsToUpdate.length +
        meetingsToDelete.length;
      if (formOK && numChanges > 0) {
        // now post the data...
        var _this = this;
        let data_for_post = {
          courseOfferingId: this.editCourseOfferingData.courseOfferingId,
          delete: meetingsToDelete,
          update: meetingsToUpdate,
          create: meetingsToCreate
        };
        // https://stackoverflow.com/questions/53714037/decoding-django-post-request-body
        // https://stackoverflow.com/questions/1208067/wheres-my-json-data-in-my-incoming-django-request
        $.ajax({
          // initialize an AJAX request
          type: "POST",
          url: "/planner/ajax/update-class-schedule/",
          dataType: "json",
          data: JSON.stringify(data_for_post),
          success: function(jsonResponse) {
            _this.editCourseOfferingData.ichairObject.meeting_times_detail =
              jsonResponse.meeting_times_detail;
            _this.editCourseOfferingData.ichairObject.meeting_times =
              jsonResponse.meeting_times;
            _this.cancelMeetingsForm();
          },
          error: function(jqXHR, exception) {
            // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
            console.log(jqXHR);
            _this.meetingFormErrorMessage =
              "Sorry, there appears to have been an error.";
          }
        });
      }
    },
    checkTimes(beginTime, endTime) {
      let beginValid = this.timeStringValid(beginTime);
      let endValid = this.timeStringValid(endTime);
      if (!(beginValid && endValid)) {
        return {
          errorMessage:
            "Beginning and ending times must be in the correct format.",
          timesOK: false
        };
      } else {
        if (!this.timeSeqOK(beginTime, endTime)) {
          return {
            errorMessage: "Ending time must be after beginning time.",
            timesOK: false
          };
        }
      }
      return {
        errorMessage: "",
        timesOK: true
      };
    },
    checkTimeConflicts(meetingSummary) {
      daySchedules = { 0: [], 1: [], 2: [], 3: [], 4: [] };
      let timesOK = true;
      meetingSummary.forEach(meeting => {
        let begin = this.convertTimeStringToInt(meeting.begin_at);
        let end = this.convertTimeStringToInt(meeting.end_at);
        daySchedules[meeting.day].forEach(meetingTime => {
          let existingBegin = meetingTime.begin;
          let existingEnd = meetingTime.end;
          if (
            (begin < existingEnd && begin > existingBegin) ||
            (end < existingEnd && end > existingBegin) ||
            (begin <= existingBegin && end >= existingEnd)
          ) {
            timesOK = false;
          }
        });
        if (timesOK) {
          daySchedules[meeting.day].push({
            begin: begin,
            end: end
          });
        }
      });
      return {
        timesOK: timesOK,
        errorMessage: timesOK
          ? ""
          : "Time blocks for a given day within a course offering cannot overlap."
      };
    },
    timeStringValid(timeString) {
      return /^([0-1]?[0-9]|2[0-3]):([0-5][0-9])(:[0-5][0-9])?$/.test(
        timeString
      );
    },
    timeSeqOK(beginTimeString, endTimeString) {
      return (
        this.convertTimeStringToInt(endTimeString) >
        this.convertTimeStringToInt(beginTimeString)
      );
    },
    convertTimeStringToInt(timeString) {
      let multiplicativeFactors = [10000, 100, 1];
      let timeSum = 0;
      let timeSplit = timeString.split(":");
      // https://www.w3schools.com/jsref/jsref_parseint.asp
      for (var i = 0; i < timeSplit.length; i++) {
        timeSum += multiplicativeFactors[i] * parseInt(timeSplit[i]);
      }
      return timeSum;
    },
    greet: function(name) {
      //console.log('Hello from ' + name + '!');
    },
    // https://stackoverflow.com/questions/44309464/hide-table-column-with-vue-js
    showColumn(col) {
      return this.headers.find(h => h.value === col).selected;
    },
    toggle(col) {
      let tempSelected = this.headers.find(h => h.value === col).selected;
      this.headers.find(h => h.value === col).selected = !tempSelected;
    }
  },
  // https://stackoverflow.com/questions/44309464/hide-table-column-with-vue-js
  computed: {
    filteredHeaders() {
      return this.headers.filter(h => h.selected);
    },
    checkboxVal(col) {
      return this.headers.find(h => h.value === col).selected;
    }
  },
  mounted: function() {
    var _this = this;
    $.ajax({
      // initialize an AJAX request
      type: "GET",
      url: "/planner/ajax/fetch-semesters/", // set the url of the request
      dataType: "json",
      data: {
        departmentId: json_data.departmentId, // add the department id to the GET parameters
        yearId: json_data.yearId
      },
      success: function(incomingData) {
        console.log(incomingData);
        _this.semesterChoices = incomingData.semester_choices;
      }
    });

  }
});
