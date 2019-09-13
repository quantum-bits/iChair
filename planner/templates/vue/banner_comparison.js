// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const
const CREATE_NEW_COURSE = -2;
const DO_NOTHING = -1;

const DELTA_ACTION_CREATE = "create"; // used for delta course offerings; note that these are actions that the registrar is being asked to
const DELTA_ACTION_UPDATE = "update"; // perform, not the actions that are being performed here on the delta objects
const DELTA_ACTION_DELETE = "delete";
const DELTA_ACTION_SET = "deltaUpdateSet"; // turn off the update
const DELTA_ACTION_UNSET = "deltaUpdateUnset"; // turn off the update

const DELTA_UPDATE_TYPE_MEETING_TIMES = "meetingTimes";
const DELTA_UPDATE_TYPE_INSTRUCTORS = "instructors";
const DELTA_UPDATE_TYPE_SEMESTER_FRACTION = "semesterFraction";
const DELTA_UPDATE_TYPE_ENROLLMENT_CAP = "enrollmentCap";

const COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT = "enrollmentCap";
const COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION = "semesterFraction";
const COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS = "instructors";
const COPY_REGISTRAR_TO_ICHAIR_ALL = "all";

var app = new Vue({
  delimiters: ["[[", "]]"],
  el: "#app",
  vuetify: new Vuetify(),
  data() {
    return {
      DELTA_UPDATE_TYPE_MEETING_TIMES: DELTA_UPDATE_TYPE_MEETING_TIMES, // so that this is available in the template....
      DELTA_UPDATE_TYPE_INSTRUCTORS: DELTA_UPDATE_TYPE_INSTRUCTORS,
      DELTA_UPDATE_TYPE_SEMESTER_FRACTION: DELTA_UPDATE_TYPE_SEMESTER_FRACTION,
      DELTA_UPDATE_TYPE_ENROLLMENT_CAP: DELTA_UPDATE_TYPE_ENROLLMENT_CAP,
      DELTA_ACTION_SET: DELTA_ACTION_SET,
      DELTA_ACTION_UNSET: DELTA_ACTION_UNSET,
      COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT: COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT,
      COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION: COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION,
      COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS: COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS,
      COPY_REGISTRAR_TO_ICHAIR_ALL: COPY_REGISTRAR_TO_ICHAIR_ALL,
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
        { text: "Credit Hours", value: "creditHours", align: "left" },
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
      console.log("inside align courses");
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
          let num_offerings = "";
          let max_num_offerings = 0;
          let credit_text = "";
          /**
           * course.choice = -1 ==> do nothing
           * course.choice = -2 ==> create new course
           * course.choice = iChair course id ==> set banner_title in iChair course to banner title (in data warehouse database)
           */
          incomingData.unmatched_courses.forEach(course => {
            unmatchedCourse = course;
            choices = [];
            if (course.ichair_courses.length === 0) {
              unmatchedCourse.choice = CREATE_NEW_COURSE; // default is to create a new course
              choices.push({
                bannerCourseId: course.banner_course.id,
                selectionId: CREATE_NEW_COURSE, //assuming actual db ids will never be negative
                text:
                  "Create a new matching course (recommended, since there is currently no matching course in iChair)"
              });
            } else {
              max_num_offerings = 0;
              unmatchedCourse.choice = DO_NOTHING; // default starts as "do nothing"
              course.ichair_courses.forEach(item => {
                if (item.number_offerings_this_year > max_num_offerings) {
                  max_num_offerings = item.number_offerings_this_year;
                  unmatchedCourse.choice = item.id; // default becomes to choose the course with the greatest # of course offerings
                }
                if (item.credit_hours == 1) {
                  credit_text = " credit hour; ";
                } else {
                  credit_text = " credit hours; ";
                }
                item.number_offerings_this_year == 1
                  ? (num_offerings = " offering ")
                  : (num_offerings = " offerings ");
                choices.push({
                  bannerCourseId: course.banner_course.id,
                  selectionId: item.id, //assuming actual db ids will never be negative
                  text:
                    item.subject +
                    " " +
                    item.number +
                    ": " +
                    item.title +
                    " (" +
                    item.credit_hours +
                    credit_text +
                    item.number_offerings_this_year +
                    num_offerings +
                    "this year)"
                });
              });
              choices.push({
                bannerCourseId: course.banner_course.id,
                selectionId: CREATE_NEW_COURSE, //assuming actual db ids will never be negative
                text:
                  "Create a new matching course (not recommended in this case)"
              });
            }
            choices.push({
              bannerCourseId: course.banner_course.id,
              selectionId: DO_NOTHING, //assuming actual db ids will never be negative
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
      this.unmatchedCourses.forEach(course => {
        if (course.choice == CREATE_NEW_COURSE) {
          dataForPost.create.push({
            title: course.banner_course.title,
            credit_hours: course.banner_course.credit_hours,
            number: course.banner_course.number,
            subject_id: course.ichair_subject_id
          });
        } else if (course.choice == DO_NOTHING) {
          console.log("do nothing: ", course.banner_course.title);
        } else {
          dataForPost.update.push({
            ichair_course_id: course.choice,
            banner_title: course.banner_course.title
          });
        }
      });
      if (dataForPost.create.length == 0 && dataForPost.update.length == 0) {
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
          console.log("response: ", jsonResponse);
          if (
            !(
              jsonResponse.updates_successful && jsonResponse.creates_successful
            )
          ) {
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
      console.log("align course offerings!");
      var _this = this;

      let dataForPost = {
        departmentId: json_data.departmentId, // add the faculty id to the GET parameters
        yearId: json_data.yearId,
        semesterIds: this.chosenSemesters
      };

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
              semesterId: course.semester_id,
              number: course.course,
              creditHours: course.credit_hours,
              name: course.course_title,
              crn: course.crn,
              schedulesMatch: course.schedules_match,
              instructorsMatch: course.instructors_match,
              semesterFractionsMatch: course.semester_fractions_match,
              enrollmentCapsMatch: course.enrollment_caps_match,
              delta: course.delta,
              ichair: course.ichair,
              banner: course.banner,
              hasIChair: course.has_ichair,
              hasBanner: course.has_banner,
              linked: course.linked,
              allOK: course.all_OK,
              errorMessage: '',
              loadsAdjustedWarning: ''
            });
          });
          _this.semesterFractionsReverse =
            incomingData.semester_fractions_reverse;
          _this.semesterFractions = incomingData.semester_fractions;
          _this.courseOfferingAlignmentPhaseReady = true;
          console.log("course offering data: ", _this.courseOfferings);
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
      console.log("edit semester fraction!");
    },
    addNewMeetingTimes(courseInfo) {
      console.log(courseInfo);
    },
    deltaUpdate(item, updateType, updateSetOrUnset) {
      // we have both an iChair course offering and a banner course offering; pass along the item so that generateUpdateDelta() has them;
      // updateType is one of:
      //  - DELTA_UPDATE_TYPE_INSTRUCTORS
      //  - DELTA_UPDATE_TYPE_MEETING_TIMES
      //  - DELTA_UPDATE_TYPE_ENROLLMENT_CAP
      //  - DELTA_UPDATE_TYPE_SEMESTER_FRACTION
      // updateOrUndo is DELTA_ACTION_UPDATE or DELTA_ACTION_UNDO_UPDATE
      //
      // https://www.w3schools.com/jsref/jsref_switch.asp

      let updateTypeOK = true;
      let deltaMods = {};
      switch (updateType) {
        case DELTA_UPDATE_TYPE_INSTRUCTORS:
          deltaMods = {
            instructors: updateSetOrUnset === DELTA_ACTION_SET ? true : false
          };
          break;
        case DELTA_UPDATE_TYPE_MEETING_TIMES:
          deltaMods = {
            meetingTimes: updateSetOrUnset === DELTA_ACTION_SET ? true : false
          };
          break;
        case DELTA_UPDATE_TYPE_ENROLLMENT_CAP:
          deltaMods = {
            enrollmentCap: updateSetOrUnset === DELTA_ACTION_SET ? true : false
          };
          break;
        case DELTA_UPDATE_TYPE_SEMESTER_FRACTION:
          deltaMods = {
            semesterFraction:
              updateSetOrUnset === DELTA_ACTION_SET ? true : false
          };
          break;
        default:
          updateTypeOK = false;
      }

      if (updateTypeOK) {
        console.log("generate delta: ", updateType);
        console.log("item", item);
        this.generateUpdateDelta(item, deltaMods, DELTA_ACTION_UPDATE);
      }
    },

    generateUpdateDelta(item, deltaMods, action) {
      // WORKING HERE: need to modify this for the other actions!!!
      // NEXT: add in other types of updates!!!

      let dataForPost = {};
      let deltaId = null;
      if (item.delta !== null) {
        deltaId = item.delta.id;
      }

      if (action === DELTA_ACTION_UPDATE) {
        dataForPost = {
          deltaMods: deltaMods,
          deltaId: deltaId,
          action: action,
          crn: item.crn,
          iChairCourseOfferingId: item.ichair.course_offering_id,
          bannerCourseOfferingId: item.banner.course_offering_id,
          semesterId: item.semesterId
        };
      }

      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/generate-update-delta/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(jsonResponse) {
          console.log("response: ", jsonResponse);
          item.delta = jsonResponse.delta;
          item.enrollmentCapsMatch =
            jsonResponse.agreement_update.max_enrollments_match ||
            item.delta.request_update_max_enrollment;
          item.instructorsMatch =
            jsonResponse.agreement_update.instructors_match ||
            item.delta.request_update_instructors;
          item.schedulesMatch =
            jsonResponse.agreement_update.meeting_times_match ||
            item.delta.request_update_meeting_times;
          item.semesterFractionsMatch =
            jsonResponse.agreement_update.semester_fractions_match ||
            item.delta.request_update_semester_fraction;
          item.allOK =
            item.enrollmentCapsMatch &&
            item.instructorsMatch &&
            item.schedulesMatch &&
            item.semesterFractionsMatch;
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
    copyRegistrarDataToiChair(item, dataToUpdate) {
      // assume for now that an iChair course offering object exists already, but maybe could generalize...(?)
      // also assume that a banner course offering exists, or else we have nothing to copy from....
      console.log("item: ", item);
      console.log('data to update: ', dataToUpdate)
      let dataForPost = {};
      let deltaId = null;
      if (item.delta !== null) {
        deltaId = item.delta.id;
      }
      dataForPost = {
        action: "update",
        // if 'update', then an ichair course offering id must be provided
        // if 'create', then the ichair course offering id should be set to null
        iChairCourseOfferingId: item.ichair.course_offering_id,
        bannerCourseOfferingId: item.banner.course_offering_id,
        deltaId: deltaId,
        propertiesToUpdate: []
      };
      if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT) {
        dataForPost.propertiesToUpdate.push("max_enrollment")
      } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION) {
        dataForPost.propertiesToUpdate.push("semester_fraction")
      } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS) {
        console.log('aligning instructors!');
        dataForPost.propertiesToUpdate.push("instructors")
      }
      // COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT
      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/copy-registrar-course-offering-data-to-ichair/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(jsonResponse) {
          console.log("response: ", jsonResponse);
          item.delta = jsonResponse.delta_response;
          item.enrollmentCapsMatch =
            jsonResponse.agreement_update.max_enrollments_match; // don't need to check item.delta.request_update_max_enrollment, since this was already sorted out by the server-side code....
          item.instructorsMatch =
            jsonResponse.agreement_update.instructors_match;
          item.schedulesMatch =
            jsonResponse.agreement_update.meeting_times_match;
          item.semesterFractionsMatch =
            jsonResponse.agreement_update.semester_fractions_match;
          item.allOK =
            item.enrollmentCapsMatch &&
            item.instructorsMatch &&
            item.schedulesMatch &&
            item.semesterFractionsMatch;
          item.ichair = jsonResponse.course_offering_update;

          if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS || dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_ALL) {
            if (jsonResponse.offering_instructors_copied_successfully === false) {
              console.log('error copying instructors!')
              item.errorMessage = "There was an error trying to copy the instructor data from the registrar's database.  It may be that one or more of the iChair instructors does not exist in the Registrar's database.  If this seems incorrect, please contact the iChair administrator."
            }
            if (jsonResponse.load_manipulation_performed === true) {
              console.log('loads were adjusted!')
              item.loadsAdjustedWarning = "One or more loads were adjusted automatically in the process of copying instructors from the registrar's database.  You may wish to check that this was done correctly."
            }
            // WORKING HERE....
            // check if offering_instructors_copied_successfully === true; if not, display an error message (which should be added as a new property
            // to the item....)
            // this can happen if the iChair version of the instructor doesn't match the banner version (e.g., "Math TBA" or an instructor without a pidm)
            // tell the user they can't use the copy feature in this case and can try to edit by hand instead

            // also, in general, add a comment that the loads may need to be tweaked (or maybe flash up a dialog at the end to allow the user
            // to specify loads right away...?)
          }

        },
        error: function(jqXHR, exception) {
          // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
          console.log(jqXHR);
        }
      });

      // action = json_data['action'] ('create' or 'update')
      // course_offering_properties = json_data['courseOfferingProperties']
      // banner_course_offering_id = json_data['bannerCourseOfferingId']
      // ichair_course_offering_id = course_offering_properties.course_offering_id
      // delta_id = json_data['deltaId']
      // 'max_enrollment' within courseOfferingProperties

      //ajax/copy-registrar-course-offering-data-to-ichair/
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
    },
    // https://github.com/vuetifyjs/vuetify/issues/3897
    indexedCourseOfferings() {
      return this.courseOfferings.map((item, index) => ({
        id: index,
        ...item
      }));
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
