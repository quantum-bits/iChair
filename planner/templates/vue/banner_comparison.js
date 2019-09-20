// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const
const CREATE_NEW_COURSE = -2;
const DO_NOTHING = -1;

const CREATE_NEW_COURSE_OFFERING = -2;
const DELETE_BANNER_COURSE_OFFERING = -3;

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
const COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES = "meetingTimes";
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
      DELTA_ACTION_CREATE: DELTA_ACTION_CREATE,
      DELTA_ACTION_UPDATE: DELTA_ACTION_UPDATE,
      DELTA_ACTION_DELETE: DELTA_ACTION_DELETE,
      COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT: COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT,
      COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION: COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION,
      COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS: COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS,
      COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES: COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES,
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
      newCourseOfferingDialog: false, // true when the new course offering dialog is being displayed
      courseChoices: [], // used in the new course offering dialog when choosing which course to associate with a course offering that is about to be created
      courseChoice: null, // the course chosen in the new course offering dialog
      newCourseOfferingDialogItem: null, // the courseOfferings 'item' relevant for the new course offering dialog
      newCourseOfferingDialogCourseText: "", // some text displayed in the new course offering dialog
      newCourseOfferingDialogErrorMessage: "", // error message used in the new course offering dialog
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
                    item.course +
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
          //   course.ichair_courses.forEach(item => {
          //     if (item.number_offerings_this_year > max_num_offerings) {
          //       max_num_offerings = item.number_offerings_this_year;
          //       unmatchedCourse.choice = item.id; // default becomes to choose the course with the greatest # of course offerings
          //     }
          //     if (item.credit_hours == 1) {
          //       credit_text = " credit hour; ";
          //     } else {
          //       credit_text = " credit hours; ";
          //     }
          //     item.number_offerings_this_year == 1
          //       ? (num_offerings = " offering ")
          //       : (num_offerings = " offerings ");
          //     choices.push({
          //       bannerCourseId: course.banner_course.id,
          //       selectionId: item.id, //assuming actual db ids will never be negative
          //       text:
          //         item.subject +
          //         " " +
          //         item.number +
          //         ": " +
          //         item.title +
          //         " (" +
          //         item.credit_hours +
          //         credit_text +
          //         item.number_offerings_this_year +
          //         num_offerings +
          //         "this year)"
          //     });
          //   });
          //   choices.push({
          //     bannerCourseId: course.banner_course.id,
          //     selectionId: CREATE_NEW_COURSE, //assuming actual db ids will never be negative
          //     text:
          //       "Create a new matching course (not recommended in this case)"
          //   });
          // }
          // choices.push({
          //   bannerCourseId: course.banner_course.id,
          //   selectionId: DO_NOTHING, //assuming actual db ids will never be negative
          //   text: "Do nothing for now...."
          // });
          // unmatchedCourse.choices = choices;
          // _this.unmatchedCourses.push(unmatchedCourse);

          // https://stackoverflow.com/questions/3590685/accessing-this-from-within-an-objects-inline-function
          incomingData.course_data.forEach(course => {
            let ichairChoices = [];
            let showIChairRadioSelect = false;

            if (!course.has_ichair) {
              course.ichair_options.forEach(ichairOption => {
                let creditText =
                  ichairOption.credit_hours === 1
                    ? " credit hour"
                    : " credit hours";
                let meetingTimes =
                  ichairOption.meeting_times.length === 0 ? ")" : "; ";
                ichairOption.meeting_times.forEach(mT => {
                  meetingTimes = meetingTimes + mT + "; ";
                });
                if (meetingTimes.length >= 2) {
                  // https://tecadmin.net/remove-last-character-from-string-in-javascript/
                  console.log("meeting times:", meetingTimes);
                  meetingTimes = meetingTimes.substring(
                    0,
                    meetingTimes.length - 2
                  ); // get rid of last trailing "; "
                  meetingTimes = meetingTimes + ")";
                }
                ichairChoices.push({
                  selectionId: ichairOption.course_offering_id,
                  text:
                    "Link with: " +
                    ichairOption.course +
                    ": " +
                    ichairOption.course_title +
                    " (" +
                    ichairOption.credit_hours +
                    creditText +
                    meetingTimes +
                    " (it can be edited afterward)"
                });
              });
              ichairChoices.push({
                selectionId: CREATE_NEW_COURSE_OFFERING, //assuming that course offering ids are always non-negative
                text:
                  "Create a new iChair course offering to match the Registrar's version"
              });
              ichairChoices.push({
                selectionId: DELETE_BANNER_COURSE_OFFERING,
                text: "Request that the Registrar delete this course offering"
              });

              if (course.delta === null) {
                showIChairRadioSelect = true;
              } else if (
                course.delta.requested_action === DELTA_ACTION_DELETE
              ) {
                showIChairRadioSelect = false;
              } else {
                showIChairRadioSelect = true;
              }
            }

            let bannerChoices = [];
            let showBannerRadioSelect = false;
            if (!course.has_banner) {
              course.banner_options.forEach(bannerOption => {
                let creditText =
                  bannerOption.credit_hours === 1
                    ? " credit hour"
                    : " credit hours";
                let meetingTimes =
                  bannerOption.meeting_times.length === 0 ? ")" : "; ";
                bannerOption.meeting_times.forEach(mT => {
                  meetingTimes = meetingTimes + mT + "; ";
                });
                if (meetingTimes.length >= 2) {
                  // https://tecadmin.net/remove-last-character-from-string-in-javascript/
                  console.log("meeting times:", meetingTimes);
                  meetingTimes = meetingTimes.substring(
                    0,
                    meetingTimes.length - 2
                  ); // get rid of last trailing "; "
                  meetingTimes = meetingTimes + ")";
                }
                bannerChoices.push({
                  selectionId: bannerOption.course_offering_id,
                  text:
                    "Link with: " +
                    bannerOption.course +
                    ": " +
                    bannerOption.course_title +
                    " (CRN " +
                    bannerOption.crn +
                    "; " +
                    bannerOption.credit_hours +
                    creditText +
                    meetingTimes
                });
              });
              bannerChoices.push({
                selectionId: CREATE_NEW_COURSE_OFFERING, //assuming that course offering ids are always non-negative
                text:
                  "Request that the registrar create a new course offering to match this iChair course offering"
              });

              if (course.delta === null) {
                showBannerRadioSelect = true;
              } else if (
                course.delta.requested_action === DELTA_ACTION_CREATE
              ) {
                showBannerRadioSelect = false;
              } else {
                showBannerRadioSelect = true;
              }
            }

            _this.courseOfferings.push({
              semester: course.semester,
              semesterId: course.semester_id,
              termCode: course.term_code,
              course: course.course,
              creditHours: course.credit_hours,
              name: course.course_title,
              crn: course.crn,
              schedulesMatch: course.schedules_match,
              instructorsMatch: course.instructors_match,
              semesterFractionsMatch: course.semester_fractions_match,
              enrollmentCapsMatch: course.enrollment_caps_match,
              ichairSubjectId: course.ichair_subject_id,
              delta: course.delta,
              ichair: course.ichair,
              ichairOptions: course.ichair_options, //these are potential iChair matches, which might be there if hasIChair is false
              ichairChoices: ichairChoices, // used for radio select if the user going to choose from among iChair options
              ichairChoice: null, //used by a radio select to choose one of the ichairChoices
              bannerOptions: course.banner_options, //these are potential iChair matches, which might be there if hasIChair is false
              bannerChoices: bannerChoices, // used for radio select if the user going to choose from among iChair options
              bannerChoice: null, //used by a radio select to choose one of the ichairChoices
              showCourseOfferingRadioSelect: showIChairRadioSelect,
              showBannerCourseOfferingRadioSelect: showBannerRadioSelect,
              banner: course.banner,
              hasIChair: course.has_ichair,
              hasBanner: course.has_banner,
              linked: course.linked,
              allOK: course.all_OK,
              index: course.index, // used as an item-key in the table
              errorMessage: "",
              loadsAdjustedWarning: "",
              classroomsUnassignedWarning: ""
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
    deactivateScheduleRightArrow(item) {
      if (item.delta !== null) {
        if (
          item.delta.requested_action === DELTA_ACTION_CREATE &&
          !item.delta.request_update_meeting_times
        ) {
          return false;
        }
      }
      return item.schedulesMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateScheduleLeftArrow(item) {
      return item.schedulesMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateInstructorsRightArrow(item) {
      if (item.delta !== null) {
        if (
          item.delta.requested_action === DELTA_ACTION_CREATE &&
          !item.delta.request_update_instructors
        ) {
          return false;
        }
      }
      return item.instructorsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateInstructorsLeftArrow(item) {
      return item.instructorsMatch || !item.hasIChair || !item.hasBanner;
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
    onCourseOfferingOptionChosen(item) {
      var _this = this;
      console.log("item chosen!", item.ichairChoice);
      let dataForPost = {};
      if (item.ichairChoice === CREATE_NEW_COURSE_OFFERING) {
        console.log("create a new course offering!");
        this.getCoursesForCourseOffering(item);
      } else if (item.ichairChoice === DELETE_BANNER_COURSE_OFFERING) {
        console.log("delete banner course offering!");
        // create a delta "delete" object

        dataForPost = {
          deltaMods: {
            instructors: false,
            meetingTimes: false,
            enrollmentCap: false,
            semesterFraction: false
          }, // request all delta mods by default when issuing a "create" request to the registrar
          deltaId: null, // shouldn't exist at this point, since we are creating a new delta object
          action: DELTA_ACTION_DELETE,
          crn: item.crn, // asking the registrar to delete this CRN
          iChairCourseOfferingId: null, // don't have one; we're asking the registrar to delete a course offering b/c it doesn't correspond to one in iChair
          bannerCourseOfferingId: item.banner.course_offering_id, // this is the banner course offering that we are requesting be deleted
          semesterId: item.semesterId
        };
        item.showCourseOfferingRadioSelect = false;
      } else {
        console.log("add existing iChair course offering");
        // now need to pop this item out of the list of this.courseOfferings
        // add this as the ichair element for this particular item
        item.showCourseOfferingRadioSelect = false;
        item.ichairOptions.forEach(iChairOption => {
          if (iChairOption.course_offering_id === item.ichairChoice) {
            item.ichair = iChairOption; //this version of the iChair object has a few extra properties compared to normal, but that's not a problem....
          }
        });
        item.hasIChair = true;
        item.linked = true; // not sure if this is used anywhere, but OK....
        // generate a delta object for the item; not necessary, strictly speaking, but then we can also
        // use the endpoint to check the agreement between the bco and the ico....
        dataForPost = {
          deltaMods: {}, // don't request any delta mods at this point, just create the delta object
          deltaId: null, // shouldn't exist at this point, since we have only just linked the iChair course offering with the Banner one
          action: DELTA_ACTION_UPDATE,
          crn: item.crn,
          iChairCourseOfferingId: item.ichair.course_offering_id,
          bannerCourseOfferingId: item.banner.course_offering_id,
          semesterId: item.semesterId
        };
        this.removeUnlinkedIChairItemFromCourseOfferings(
          item.banner.course_offering_id,
          item.ichair.course_offering_id
        );
      }
      if (item.ichairChoice !== CREATE_NEW_COURSE_OFFERING) {
        $.ajax({
          // initialize an AJAX request
          type: "POST",
          url: "/planner/ajax/generate-update-delta/",
          dataType: "json",
          data: JSON.stringify(dataForPost),
          success: function(jsonResponse) {
            console.log("in success: ", dataForPost);
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
            console.log("item after delta update!", item);
            console.log("all course offerings: ", _this.courseOfferings);
            //_this.popUnlinkedItemFromCourseOfferings(item.ichair.course_offering_id);
          },
          error: function(jqXHR, exception) {
            // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
            console.log(jqXHR);
            _this.showCreateUpdateErrorMessage();
            console.log("in error: ", dataForPost);
            //_this.meetingFormErrorMessage =
            //  "Sorry, there appears to have been an error.";
          }
        });
      }
    },

    getCoursesForCourseOffering(item) {
      // find the iChair courses that could correspond to a course offering that we wish to create;
      // this is the first step in creating the new course offering
      console.log(item);
      var _this = this;
      // find the possible course objects that could be a match
      let courseProperties = {
        number: item.banner.number,
        ichairSubjectId: item.ichairSubjectId,
        title: item.banner.course_title,
        creditHours: item.creditHours,
        semesterId: item.semesterId
      };
      $.ajax({
        // first check to see which course objects are candidates for this course offering
        type: "POST",
        url: "/planner/ajax/get-courses/",
        dataType: "json",
        data: JSON.stringify(courseProperties),
        success: function(jsonResponse) {
          console.log("in success: ", courseProperties);
          console.log("response: ", jsonResponse);
          let courseList = jsonResponse.courses;
          if (courseList.length === 0) {
            // there are no matches for the course in the iChair database, so go ahead and create a new one
            console.log(
              "no match for this course; creating a new one before creating the course offering...."
            );
            _this.createNewCourse(item);
          } else if (courseList.length === 1) {
            let course = courseList[0];
            if (
              courseProperties.title === course.title ||
              courseProperties.title === course.banner_title
            ) {
              // we have found the unique course in the iChair database that corresponds to this banner course offering;
              // now create the course offering
              _this.createNewCourseOffering(item, course.id);
            }
          } else {
            // there are either zero or more than one options that exist in the iChair database for the course offering that
            // we are attempting to create; give the user some options for how to proceed
            courseList.forEach(courseOption => {
              let creditText =
                courseOption.credit_hours === 1
                  ? " credit hour; "
                  : " credit hours; ";
              let numberOfferingsText =
                courseOption.number_offerings_this_year === 1
                  ? " offering in " + courseOption.year_name
                  : " offerings in " + courseOption.year_name;
              if (
                courseProperties.title === courseOption.title ||
                courseProperties.title === courseOption.banner_title
              ) {
                _this.courseChoice = courseOption.id; // this option seems like a match
              }
              _this.courseChoices.push({
                selectionId: courseOption.id,
                text:
                  "Use:  " +
                  courseOption.subject +
                  " " +
                  courseOption.number +
                  " - " +
                  courseOption.title +
                  " (" +
                  courseOption.credit_hours +
                  creditText +
                  courseOption.number_offerings_this_year +
                  numberOfferingsText +
                  ")"
              });
            });
            _this.courseChoices.push({
              selectionId: CREATE_NEW_COURSE, //assuming that course ids are always non-negative
              text:
                "Create a new iChair course to match the Registrar's version (you probably do not want to do this)"
            });

            console.log(_this.courseChoices);
            let creditText =
              item.creditHours === 1 ? " credit hour)" : " credit hours)";

            _this.newCourseOfferingDialogCourseText =
              item.banner.course +
              " - " +
              item.banner.course_title +
              " (" +
              item.creditHours +
              creditText;
            // https://scotch.io/bar-talk/copying-objects-in-javascript
            // using this approach to make the copy so that we don't risk problems later when we set it back to null
            _this.newCourseOfferingDialogItem = JSON.parse(JSON.stringify(item));
            
            
            item;
            _this.newCourseOfferingDialog = true;
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

    submitCourseChoice() {
      // stored the courseOfferings 'item' in this.newCourseOfferingDialogItem; 
      // trick to copy the item....
      let item = JSON.parse(JSON.stringify(this.newCourseOfferingDialogItem));
      let choice = this.courseChoice;
      if (choice === null) {
        this.newCourseOfferingDialogErrorMessage = "Please select one of the options."
      } else if (choice === CREATE_NEW_COURSE) {
        console.log('creating a new course for this course offering....');
        this.createNewCourse(item);
      } else {
        console.log('all appears to be good...creating the course offering!');
        // createNewCourseOffering with this item, but first do some clean-up
        this.cancelCourseOfferingDialog();
        this.createNewCourseOffering(item, choice);
      }
    },

    cancelCourseOfferingDialog() {
      this.newCourseOfferingDialogErrorMessage = "";
      this.courseChoice = null;
      this.courseChoices = [];
      this.newCourseOfferingDialog = false;
      //reset the choice change that launched the dialog in the first place
      this.courseOfferings.forEach(item => {
        if (item.index === this.newCourseOfferingDialogItem.index) {
          item.ichairChoice = null;
        }
      })
      this.newCourseOfferingDialogItem = null; // we had made a copy of the item (using the JSON.parse() trick), so we're OK to set it to null
      console.log('list of course offerings:', this.courseOfferings);
    },

    createNewCourse(item) {
      // no course options were found for the course offering that we are attempting to create, so we first
      // need to create the course, after which we will create the associated course offering
      var _this = this;
      let dataForPost = {
        create: [],
        update: []
      };
      dataForPost.create.push({
        title: item.banner.course_title,
        credit_hours: item.creditHours,
        number: item.banner.number,
        subject_id: item.ichairSubjectId
      });

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
            console.log("there was an error in trying to create this course!");
          } else {
            if (jsonResponse.created_course_ids.length === 1) {
              // we have successfully created the new course, so now proceed to associate the course offering with it....
              _this.createNewCourseOffering(
                item,
                jsonResponse.created_course_ids[0]
              );
            } else {
              console.log(
                "there were more or fewer than one course created! course id(s): ",
                jsonResponse.created_course_ids
              );
            }
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

    createNewCourseOffering(item, courseId) {
      // Create a new course offering in iChair, with properties specified by the Banner course offering.
      // Note that the 'item' that is passed in may be the actual element of this.courseOfferings, or it may be a copy,
      // depending on how we ended up in this method.
      // Thus, when all is said and done, will need to go into this.courseOfferings and search for the item to make
      // updates to it.
      console.log("create course offering!");
      console.log("item: ", item);
      console.log("course id: ", courseId);

      var _this = this;

      // NEED TO REMEMBER to hide the radio select choices in the item when all is said and done(!)
      //need to warn the user that loads have been set automatically
      let dataForPost = {
        courseId: courseId,
        bannerCourseOfferingId: item.banner.course_offering_id,
        semesterFraction: item.banner.semester_fraction,
        maxEnrollment: item.banner.max_enrollment,
        semesterId: item.semesterId,
        crn: item.crn,
        loadAvailable: item.creditHours, //need to warn the user that this has been set automatically
        meetings: [],
        instructorDetails: []
      }
      item.banner.meeting_times_detail.forEach(meetingTime => {
        dataForPost.meetings.push({
          beginAt: meetingTime.begin_at,
          endAt: meetingTime.end_at,
          day: meetingTime.day
        })
      });
      item.banner.instructors_detail.forEach(instructorItem => {
        dataForPost.instructorDetails.push({
          pidm: instructorItem.pidm,
          isPrimary: instructorItem.is_primary
        });
      });

      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/create-course-offering/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(jsonResponse) {
          console.log("response: ", jsonResponse);
          // now need to patch up the item in this.courseOfferings....
          _this.courseOfferings.forEach(courseOfferingItem => {
            if (item.index === courseOfferingItem.index) {
              // found the one we're working on
              courseOfferingItem.delta = jsonResponse.delta;
              courseOfferingItem.ichair = jsonResponse.ichair_course_offering_data;
              courseOfferingItem.enrollmentCapsMatch = jsonResponse.agreement_update.max_enrollments_match;
              courseOfferingItem.instructorsMatch = jsonResponse.agreement_update.instructors_match;
              courseOfferingItem.schedulesMatch = jsonResponse.agreement_update.meeting_times_match;
              courseOfferingItem.semesterFractionsMatch = jsonResponse.agreement_update.semester_fractions_match;
              courseOfferingItem.allOK =
                courseOfferingItem.enrollmentCapsMatch &&
                courseOfferingItem.instructorsMatch &&
                courseOfferingItem.schedulesMatch &&
                courseOfferingItem.semesterFractionsMatch;
              courseOfferingItem.hasIChair = true;
              courseOfferingItem.linked = true;
              courseOfferingItem.showCourseOfferingRadioSelect = false;

              if (jsonResponse.instructors_created_successfully === false) {
                console.log("error copying instructors!");
                courseOfferingItem.errorMessage =
                  "There was an error trying to copy the instructor data from the registrar's database.  It may be that one or more of the instructors does not yet exist in the iChair database.  If this seems incorrect, please contact the iChair administrator.";
              }
              if (jsonResponse.load_manipulation_performed === true) {
                console.log("loads were adjusted!");
                courseOfferingItem.loadsAdjustedWarning =
                  "One or more loads were adjusted automatically in the process of copying instructors from the registrar's database.  You may wish to check that this was done correctly.";
              }
              if (jsonResponse.classrooms_unassigned === true) {
                console.log("schedules assigned without classrooms!");
                courseOfferingItem.classroomsUnassignedWarning =
                  "One or more meeting times were scheduled within iChair, but without rooms being assigned.  If you know the appropriate room(s), you may wish to correct this.";
              }
            }
          });
        },
        error: function(jqXHR, exception) {
          // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
          console.log(jqXHR);
          //_this.meetingFormErrorMessage =
          //  "Sorry, there appears to have been an error.";
        }
      });

    },

    removeChoice(choice, courseOfferingId) {
      return choice.selectionId === courseOfferingId;
    },
    removeOption(option, courseOfferingId) {
      return option.course_offering_id === courseOfferingId;
    },
    removeChoicesAndOptions(bannerCourseOfferingId, iChairCourseOfferingId) {
      // used after a banner course offering and an iChair course offering have been linked;
      // removes these course offerings from the list of options for other course offerings
      this.courseOfferings.forEach(item => {
        item.bannerChoices = item.bannerChoices.filter(
          choice => !this.removeChoice(choice, bannerCourseOfferingId)
        );
      });
      this.courseOfferings.forEach(item => {
        item.ichairChoices = item.ichairChoices.filter(
          choice => !this.removeChoice(choice, iChairCourseOfferingId)
        );
      });
      this.courseOfferings.forEach(item => {
        item.bannerOptions = item.bannerOptions.filter(
          option => !this.removeOption(option, bannerCourseOfferingId)
        );
      });
      this.courseOfferings.forEach(item => {
        item.ichairOptions = item.ichairOptions.filter(
          option => !this.removeOption(option, iChairCourseOfferingId)
        );
      });
    },
    removeIChairCourseOffering(courseOffering, iChairCourseOfferingId) {
      let returnValue = false;
      if (!courseOffering.hasBanner && courseOffering.hasIChair) {
        if (
          courseOffering.ichair.course_offering_id === iChairCourseOfferingId
        ) {
          returnValue = true;
        }
      }
      return returnValue;
    },
    removeUnlinkedIChairItemFromCourseOfferings(
      bannerCourseOfferingId,
      iChairCourseOfferingId
    ) {
      // this method is used after an iChair course offering is linked up with a banner course offering;
      // the iChair course offering was previously in the list, but now it should be popped out;
      // also, the banner course offering should be deleted as a choice in bannerOptions (listing of banner course objects) and
      // bannerChoices (listing used for a radio select), and likewise for the (now linked) iChair course offering
      console.log("popping iChair item that is now linked....");
      console.log("course offerings length: ", this.courseOfferings.length);
      this.courseOfferings = this.courseOfferings.filter(
        courseOffering =>
          !this.removeIChairCourseOffering(
            courseOffering,
            iChairCourseOfferingId
          )
      );
      this.removeChoicesAndOptions(
        bannerCourseOfferingId,
        iChairCourseOfferingId
      );
    },
    onBannerCourseOfferingOptionChosen(item) {
      console.log("banner course offering chosen!", item.bannerChoice);
      console.log("item: ", item);
      // now need to link the course to the corresponding banner course offering
      // then clean up and delete it as a choice from other ichair course offerings, etc., and pop the unlinked course out of the list
      var _this = this;
      let dataForPost = {};
      if (item.bannerChoice === CREATE_NEW_COURSE_OFFERING) {
        console.log("request that the registrar create a new course offering!");
        // WORKING HERE now need to create a new course offering

        dataForPost = {
          deltaMods: {
            instructors: true,
            meetingTimes: true,
            enrollmentCap: true,
            semesterFraction: true
          }, // request all delta mods by default when issuing a "create" request to the registrar
          deltaId: null, // shouldn't exist at this point, since we have only just linked the Banner course offering with the iChair one
          action: DELTA_ACTION_CREATE,
          crn: null, // doesn't exist yet
          iChairCourseOfferingId: item.ichair.course_offering_id,
          bannerCourseOfferingId: null, // don't have one, since we're requesting that the registrar create one
          semesterId: item.semesterId
        };
        item.showBannerCourseOfferingRadioSelect = false;
      } else {
        console.log("add existing Banner course offering");
        // now need to pop this item out of the list of this.courseOfferings
        // add this as the banner element for this particular item; also, add in the crn
        console.log(
          "radio select before: ",
          item.showBannerCourseOfferingRadioSelect
        );
        item.showBannerCourseOfferingRadioSelect = false;
        console.log(
          "radio select after: ",
          item.showBannerCourseOfferingRadioSelect
        );
        item.bannerOptions.forEach(bannerOption => {
          if (bannerOption.course_offering_id === item.bannerChoice) {
            item.banner = bannerOption; //this version of the iChair object has a few extra properties compared to normal, but that's not a problem....
            item.crn = bannerOption.crn;
            item.course = bannerOption.course;
            item.name = bannerOption.course_title;
          }
        });
        console.log("item: ", item);
        item.hasBanner = true;
        item.linked = true; // not sure if this is used anywhere, but OK....
        // generate a delta object for the item; not necessary, strictly speaking, but then we can also
        // use the endpoint to check the agreement between the bco and the ico....
        dataForPost = {
          deltaMods: {}, // don't request any delta mods at this point, just create the delta object
          deltaId: null, // shouldn't exist at this point, since we have only just linked the Banner course offering with the iChair one
          action: DELTA_ACTION_UPDATE,
          crn: item.crn,
          iChairCourseOfferingId: item.ichair.course_offering_id,
          bannerCourseOfferingId: item.banner.course_offering_id,
          semesterId: item.semesterId
        };
        this.removeUnlinkedBannerItemFromCourseOfferings(
          item.banner.course_offering_id,
          item.ichair.course_offering_id
        );
        console.log("back from popping item....");
        console.log("data for post: ", dataForPost);
      }

      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/generate-update-delta/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(jsonResponse) {
          console.log("in success: ", dataForPost);
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
          console.log("item after delta update!", item);
          console.log("all course offerings: ", _this.courseOfferings);
          //_this.popUnlinkedItemFromCourseOfferings(item.ichair.course_offering_id);
        },
        error: function(jqXHR, exception) {
          // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
          console.log(jqXHR);
          _this.showCreateUpdateErrorMessage();
          console.log("in error: ", dataForPost);
          //_this.meetingFormErrorMessage =
          //  "Sorry, there appears to have been an error.";
        }
      });
    },

    removeBannerCourseOffering(courseOffering, bannerCourseOfferingId) {
      let returnValue = false;
      if (courseOffering.hasBanner && !courseOffering.hasIChair) {
        if (
          courseOffering.banner.course_offering_id === bannerCourseOfferingId
        ) {
          returnValue = true;
        }
      }
      return returnValue;
    },
    removeUnlinkedBannerItemFromCourseOfferings(
      bannerCourseOfferingId,
      iChairCourseOfferingId
    ) {
      // this method is used after a Banner course offering is linked up with an iChair course offering;
      // the Banner course offering was previously in the list, but now it should be popped out;
      // also, the banner course offering should be deleted as a choice in bannerOptions (listing of banner course objects) and
      // bannerChoices (listing used for a radio select), and likewise for the (now linked) iChair course offering
      console.log("popping banner item that is now linked....");
      console.log("course offerings length: ", this.courseOfferings.length);
      this.courseOfferings = this.courseOfferings.filter(
        courseOffering =>
          !this.removeBannerCourseOffering(
            courseOffering,
            bannerCourseOfferingId
          )
      );
      this.removeChoicesAndOptions(
        bannerCourseOfferingId,
        iChairCourseOfferingId
      );
    },

    //courseOfferings
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
    deleteDelta(item) {
      // delete the delta object associated with the item;
      // this is used to delete delta objects that are of the "create" and "delete" type;
      // at this point we don't bother deleting delta objects of the "update" variety, since all of their
      // properties can just be set to false, and then they basically don't do anything
      let deltaAction = item.delta.requested_action; // need this later in order to know the appropriate way to refresh the page....
      let dataForPost = {
        deltaId: item.delta.id
      };
      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/delete-delta/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(jsonResponse) {
          console.log("response: ", jsonResponse);
          item.delta = null;
          item.enrollmentCapsMatch =
            jsonResponse.agreement_update.max_enrollments_match;
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
          if (deltaAction === DELTA_ACTION_CREATE) {
            // we deleted a request to create a new banner course offering, so now we need to show the list of banner choices again
            item.bannerChoice = null;
            item.showBannerCourseOfferingRadioSelect = true;
          } else if (deltaAction === DELTA_ACTION_DELETE) {
            // we deleted a request to delete the existing banner course offering, so now we need to show the list of iChair choices again
            item.ichairChoice = null;
            item.showCourseOfferingRadioSelect = true;
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
    deltaUpdate(item, updateType, updateSetOrUnset) {
      // pass along the item so that generateUpdateDelta() has access to the information about the course offering, etc.
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
        this.generateUpdateDelta(item, deltaMods);
      }
    },

    generateUpdateDelta(item, deltaMods) {
      // this method is used to generate a new delta object of requested_action "update" type, or to (confusingly) update an existing
      // delta object of any requested_action type ("update", "create" or "delete");
      // creating a new delta object of requested_action "create" type is handled in another method; likewise for the "delete" type
      //
      // thus, if a delta object does not already exist in the item, we will generate a new one, with requested_action being "update"
      //
      // the delta object has information about what type delta "requested_action" type it is, if the delta object exists....
      // options for the requested action are:
      //  - DELTA_ACTION_CREATE
      //  - DELTA_ACTION_UPDATE
      //  - DELTA_ACTION_DELETE

      let dataForPost = {};
      if (item.delta !== null) {
        // there is an existing delta object, so we are updating that object; it can be of requested_action type "create", "update" or "delete"
        if (item.delta.requested_action === DELTA_ACTION_UPDATE) {
          dataForPost = {
            deltaMods: deltaMods,
            deltaId: item.delta.id,
            action: item.delta.requested_action, // action we are requesting of the registrar
            crn: item.crn,
            iChairCourseOfferingId: item.ichair.course_offering_id,
            bannerCourseOfferingId: item.banner.course_offering_id,
            semesterId: item.semesterId
          };
        } else if (item.delta.requested_action === DELTA_ACTION_CREATE) {
          dataForPost = {
            deltaMods: deltaMods,
            deltaId: item.delta.id,
            action: item.delta.requested_action, // action we are requesting of the registrar
            crn: item.crn,
            iChairCourseOfferingId: item.ichair.course_offering_id,
            bannerCourseOfferingId: null, // no banner course offering exists, since we are requesting that the registrar create a new one
            semesterId: item.semesterId
          };
        } else if (item.delta.requested_action === DELTA_ACTION_DELETE) {
          console.log("deleting!");
        }
      } else {
        // if there is no delta object, we are adding a new delta object, with requested_action (of the registrar) being "update"
        dataForPost = {
          deltaMods: deltaMods,
          deltaId: null,
          action: DELTA_ACTION_UPDATE, // action we are requesting of the registrar
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
      console.log("data to update: ", dataToUpdate);
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
        dataForPost.propertiesToUpdate.push("max_enrollment");
      } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION) {
        dataForPost.propertiesToUpdate.push("semester_fraction");
      } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS) {
        console.log("aligning instructors!");
        dataForPost.propertiesToUpdate.push("instructors");
      } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES) {
        console.log("aligning instructors!");
        dataForPost.propertiesToUpdate.push("meeting_times");
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

          if (jsonResponse.offering_instructors_copied_successfully === false) {
            console.log("error copying instructors!");
            item.errorMessage =
              "There was an error trying to copy the instructor data from the registrar's database.  It may be that one or more of the iChair instructors does not exist in the Registrar's database.  If this seems incorrect, please contact the iChair administrator.";
          }
          if (jsonResponse.load_manipulation_performed === true) {
            console.log("loads were adjusted!");
            item.loadsAdjustedWarning =
              "One or more loads were adjusted automatically in the process of copying instructors from the registrar's database.  You may wish to check that this was done correctly.";
          }
          if (jsonResponse.classrooms_unassigned === true) {
            console.log("schedules assigned without classrooms!");
            item.classroomsUnassignedWarning =
              "One or more meeting times were scheduled within iChair, but without rooms being assigned.  If you know the appropriate room(s), you may wish to correct this.";
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
    generatePDF() {
      let deltas = [];
      this.courseOfferings.forEach(item => {
        if (item.delta !== null) {
          if (item.delta.messages_exist) {
            deltas.push({
              term_code: item.term_code,
              term_name: item.term,
              banner: item.banner,
              delta: item.course_title
            })
          }
        }
      });

      dataForPost = {
        department: 'Physics and Engineering',
        academicYear: '2019-20',
        deltas: deltas
      }

      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/generate-pdf/",
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
    filteredCourseOfferings() {
      return this.courseOfferings.filter(h);
    },
    checkboxVal(col) {
      return this.headers.find(h => h.value === col).selected;
    },
    // https://github.com/vuetifyjs/vuetify/issues/3897
    // the following is no longer being used....
    indexedCourseOfferings() {
      let indexedCourseOfferings = this.courseOfferings.map((item, index) => ({
        id: index,
        ...item
      }));
      return indexedCourseOfferings.filter(item => !item.hidden);
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
