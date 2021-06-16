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
const DELTA_UPDATE_TYPE_COMMENTS = "publicComments";
const DELTA_UPDATE_TYPE_DELIVERY_METHOD = "deliveryMethod";

const COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT = "enrollmentCap";
const COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION = "semesterFraction";
const COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS = "instructors";
const COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES = "meetingTimes";
const COPY_REGISTRAR_TO_ICHAIR_COMMENTS = "publicComments";
const COPY_REGISTRAR_TO_ICHAIR_DELIVERY_METHOD = "deliveryMethod";
const COPY_REGISTRAR_TO_ICHAIR_ALL = "all";

const NO_ROOM_SELECTED_ID = Number.NEGATIVE_INFINITY;
const NO_DELIVERY_METHOD_SELECTED_ID = Number.NEGATIVE_INFINITY;

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
      DELTA_UPDATE_TYPE_COMMENTS: DELTA_UPDATE_TYPE_COMMENTS,
      DELTA_UPDATE_TYPE_DELIVERY_METHOD: DELTA_UPDATE_TYPE_DELIVERY_METHOD,
      DELTA_ACTION_SET: DELTA_ACTION_SET,
      DELTA_ACTION_UNSET: DELTA_ACTION_UNSET,
      DELTA_ACTION_CREATE: DELTA_ACTION_CREATE,
      DELTA_ACTION_UPDATE: DELTA_ACTION_UPDATE,
      DELTA_ACTION_DELETE: DELTA_ACTION_DELETE,
      COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT: COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT,
      COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION: COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION,
      COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS: COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS,
      COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES: COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES,
      COPY_REGISTRAR_TO_ICHAIR_COMMENTS: COPY_REGISTRAR_TO_ICHAIR_COMMENTS,
      COPY_REGISTRAR_TO_ICHAIR_DELIVERY_METHOD: COPY_REGISTRAR_TO_ICHAIR_DELIVERY_METHOD,
      COPY_REGISTRAR_TO_ICHAIR_ALL: COPY_REGISTRAR_TO_ICHAIR_ALL,
      semesterFractionsReverse: {}, // used to convert
      semesterFractions: {},
      semesterFractionsDropdown: [], // used for a drop-down menu
      choosingSemesters: true, // set to false once semesters have been chosen to work on
      semesterChoices: [], // filled in via an ajax request after the component is mounted
      roomRequestsAllowed: false, // true if room requests are allowed for one of the chosen semesters
      includeRoomComparisons: true, // can be set to true by the user if they would like to request room edits
      facultyChoices: [], // faculty available to teach courses
      roomChoices: [], // rooms available for course offerings
      extraDepartmentalCourseChoices: [], // courses to possible include in schedule editing
      extraDepartmentalSubjectAndCourseChoices: [], // subjects and courses from which to choose for schedule editing
      extraDepartmentalSubjectChoices: [], // subjects from which to choose for schedule editing
      // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/NEGATIVE_INFINITY
      extraDepartmentalSubjectChoice: Number.NEGATIVE_INFINITY, // choice for a subject id to look at
      extraDepartmentalCourseChoice: Number.NEGATIVE_INFINITY, // choice for a course id to look at
      extraCourseDialogChoices: [], // used in the extra-departmental course-choosing dialog (choices in a drop-down)
      selectedExtraCoursesInDialog: [], // used in the extra-departmental course-choosing dialog (choices selected from a drop-down)
      searchOtherCoursesDialog: false, // set to true when using the dialog to choose extra-departmental courses
      noSemestersChosenDialog: false, // set to true when displaying an error saying that no semesters have been chosen
      registrarCourseOfferingsExist: true, // set to false if there are no banner course offerings for any semester in the academic year under consideration
      chosenSemesters: [], // ids of semesters chosen to work on
      chosenExtraCourses: [], // extra-departmental courses chosen for schedule editing
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
        { text: "Code", value: "termCode" },
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
      showLinearProgressBar: false,
      courseOfferingAlignmentPhaseReady: false, // set to true once we're ready to start comparing course offerings
      courseOfferings: [],
      numberPrimaryInstructorsIncorrectDialog: false, // set to true in order to display a message about the number of primary instructors being incorrect
      newCourseOfferingDialog: false, // true when the new course offering dialog is being displayed
      publicCommentsDialog: false, // true when the public comments dialog is being displayed
      commentForRegistrarDialog: false, // true when the comment for registrar dialog is being displayed
      commentForRegistrar: "", // used to stored a comment for the registrar
      courseChoices: [], // used in the new course offering dialog when choosing which course to associate with a course offering that is about to be created
      courseChoice: null, // the course chosen in the new course offering dialog
      newCourseOfferingDialogItem: null, // the courseOfferings 'item' relevant for the new course offering dialog
      newCourseOfferingDialogCourseText: "", // some text displayed in the new course offering dialog
      newCourseOfferingDialogErrorMessage: "", // error message used in the new course offering dialog
      dialog: false, // true when the dialog is being displayed
      dialogTitle: "",
      editInstructorsDialog: false, // true when the dialog is being displayed
      editMeetings: [], // used to store the data in the class schedule form
      editInstructors: [], // used to store the data in the edit instructors form
      editEnrollmentCap: null, // used to store enrollment data in the class schedule form
      editLoadAvailable: null, // used to store "load available" data in the edit intructors form
      editSemesterFraction: null, // used to store semester fraction data in the class schedule form
      editDeliveryMethodId: null, // used to store delivery method data in the class schedule form
      editComments: [], // used to store the data in the public comments form
      editCourseOfferingData: {}, // used to store some data that can be used upon submitting the class schedule and public comments forms
      initialMeetingData: [], // used to hold on to the initial class schedule (before editing)
      initialEnrollmentData: null, // used to hold on to the initial enrollment data (before editing)
      initialLoadAvailableData: null, // used to hold on to the initial "load available" data (before editing)
      initialSemesterFractionData: null, // used to hold on to the initial semester fraction data (before editing)
      initialDeliveryMethodId: null, // used to hold on to the initial delivery method data (before editing)
      initialCommentData: [], // used to hold on to the initial comments (before editing)
      meetingFormErrorMessage: "", // used to display errors in the class scheduling form
      instructorFormErrorMessage: "", // used to display errors in the instructor form
      enrollmentErrorMessage: "", // used to display an enrollment error in the class scheduling form
      commentFormErrorMessage: "", // used to display errors in the public comments form
      pagination: {
        rowsPerPage: 20
      }
    };
  },
  methods: {
    launchSearchOtherCoursesDialog() {
      this.extraCourseDialogChoices = [{
        id: Number.NEGATIVE_INFINITY,
        name: '-----'
      }];
      this.selectedExtraCoursesInDialog = [];
      this.extraDepartmentalSubjectChoice = Number.NEGATIVE_INFINITY;
      this.extraDepartmentalCourseChoice = Number.NEGATIVE_INFINITY;

      this.searchOtherCoursesDialog = true;
    },
    semesterChoicesUpdated(event) {
      console.log("event:" ,event);
      console.log("semester choices: ", this.semesterChoices);
      console.log("chosen semesters: ", this.chosenSemesters);
      let roomRequestsAllowed = false;
      this.chosenSemesters.forEach(chosenSemester => {
        this.semesterChoices.forEach(semesterChoice => {
          if (semesterChoice.id === chosenSemester) {
            if (semesterChoice.allow_room_requests) {
              roomRequestsAllowed = true;
            } 
          }
        });
      });
      this.roomRequestsAllowed = roomRequestsAllowed;
    },

    onSubjectSelected(event) {
      console.log('subject id: ', event.target.value, typeof event.target.value);
      this.extraDepartmentalSubjectChoice = +event.target.value;
      console.log(this.extraDepartmentalSubjectChoice, typeof this.extraDepartmentalSubjectChoice);
      this.refreshExtraCourseDialogChoices();
    },
    onCourseSelected(event) {
      console.log('course! ', event.target.value, typeof event.target.value);
      let selectedCourseId = +event.target.value;
      this.extraDepartmentalSubjectAndCourseChoices.forEach( subject => {
        subject.courses.forEach( course => { 
          if (course.id === selectedCourseId) {
            this.selectedExtraCoursesInDialog.push({
              id: selectedCourseId,
              name: course.name
            });
          }
        });
      });
      this.extraDepartmentalCourseChoice = Number.NEGATIVE_INFINITY;
      this.refreshExtraCourseDialogChoices();
    },

    noPidmsMessage(courseOfferingItem) {
      //console.log('inside no pidms message!', courseOfferingItem);
      if (!courseOfferingItem.hasIChair) {
        return '';
      } else {
        let instructorsNoPidm = [];
        courseOfferingItem.ichair.instructors_detail.forEach( instructor => {
          if ((instructor.pidm === null) || (instructor.pidm === '')) {
            instructorsNoPidm.push(instructor);
          }
        });
        //console.log(instructorsNoPidm);
        if (instructorsNoPidm.length === 0) {
          return '';
        } else {
          let instructorNames = '';
          instructorsNoPidm.forEach( instructor => {
            if (instructorsNoPidm.length === 1) {
              instructorNames = instructor.name;
            } else if (instructorNames !== '') {
              instructorNames += ', ' + instructor.name;
            } else {
              instructorNames = instructor.name;
            }
          });
          if (instructorsNoPidm.length === 1) {
            return "The following instructor is not in the registrar's database: " + instructorNames + ". If this seems incorrect, please get in touch with the iChair administrator.";
          } else {
            return "The following instructors are not in the registrar's database: " + instructorNames + ". If this seems incorrect, please get in touch with the iChair administrator.";
          }
        }
      }
    },

    refreshExtraCourseDialogChoices() {
      // used to refresh a course drop-down list in the extra course choice dialog
      let alreadySelectedCourseIds = [];
      this.extraDepartmentalCourseChoices.forEach( course => {
        alreadySelectedCourseIds.push(course.id);
      });
      this.selectedExtraCoursesInDialog.forEach( course => {
        alreadySelectedCourseIds.push(course.id);
      });
      this.extraCourseDialogChoices = [{
        id: Number.NEGATIVE_INFINITY,
        name: '-----'
      }];
      this.extraDepartmentalSubjectAndCourseChoices.forEach( subject => {
        if (subject.id === this.extraDepartmentalSubjectChoice) {
          console.log('subject found! ', subject.abbrev);
          subject.courses.forEach( course => {
            //https://www.w3schools.com/jsref/jsref_includes_array.asp
            if (!(alreadySelectedCourseIds.includes(course.id))) {
              alreadySelectedCourseIds.push(course.id);
              this.extraCourseDialogChoices.push({
                name: course.name,
                id: course.id
              });
            }
          });
        }
      });
    },
    addExtraCoursesToList() {
      this.selectedExtraCoursesInDialog.forEach( course => {
        this.extraDepartmentalCourseChoices.push(course);
        this.chosenExtraCourses.push(course.id);
      });
      this.cancelExtraCoursesDialog();
    },
    clearFromExtraCourseList(courseId) {
      let newArray = this.selectedExtraCoursesInDialog.filter( course => course.id !== courseId );
      this.selectedExtraCoursesInDialog = JSON.parse(JSON.stringify(newArray));
      this.refreshExtraCourseDialogChoices();
    },

    cancelExtraCoursesDialog() {
      this.extraDepartmentalSubjectChoice = Number.NEGATIVE_INFINITY;
      this.extraDepartmentalCourseChoice = Number.NEGATIVE_INFINITY;
      this.extraCourseDialogChoices = [];
      this.selectedExtraCoursesInDialog =[];
      this.searchOtherCoursesDialog = false;
    },
    showCreateUpdateErrorMessage() {
      this.displayCreateUpdateErrorMessage = true;
      this.courseAlignmentPhaseReady = false;
    },

    changeRoomComparisonStatus() {
      console.log("include room comparisions? ", this.includeRoomComparisons);
      this.courseOfferingAlignmentPhaseReady = false;
      this.courseOfferings = [];
      this.alignCourseOfferings();
    },

    alignCourseOfferings() {
      if (this.chosenSemesters.length === 0) {
        this.noSemestersChosenDialog = true;
      } else {
        this.showLinearProgressBar = true;
        this.choosingSemesters = false;
        this.courseAlignmentPhaseReady = false;
        this.displayCreateUpdateErrorMessage = false;
        console.log("align course offerings!");
        var _this = this;

        let dataForPost = {
          departmentId: json_data.departmentId, // add the faculty id to the GET parameters
          yearId: json_data.yearId,
          semesterIds: this.chosenSemesters,
          extraDepartmentalCourseIdList: this.chosenExtraCourses,
          includeRoomComparisons: this.includeRoomComparisons
        };

        $.ajax({
          // initialize an AJAX request
          // seems like this should be a GET request, but I'm having trouble sending along the json data that way....
          type: "POST",
          url: "/planner/ajax/fetch-banner-comparison-data/", // set the url of the request
          dataType: "json",
          data: JSON.stringify(dataForPost),
          success: function(incomingData) {
            _this.showLinearProgressBar = false;
            console.log('available delivery methods: ', incomingData.available_delivery_methods);
            //_this.facultyChoices = incomingData.available_faculty;
            //console.log('faculty choices: ', _this.facultyChoices);
            // https://stackoverflow.com/questions/3590685/accessing-this-from-within-an-objects-inline-function
            // the noRoom choice is equivalent to a room not being selected
            let noRoom = {
                id: NO_ROOM_SELECTED_ID,
                short_name: "-----",
                capacity: -1
              };
            let noDeliveryMethod = {
              id: NO_DELIVERY_METHOD_SELECTED_ID,
              code: "",
              description: "-----",
            };
            _this.roomChoices = incomingData.available_rooms;
            _this.roomChoices.unshift(noRoom);
            _this.deliveryMethodChoices = incomingData.available_delivery_methods;
            _this.deliveryMethodChoices.unshift(noDeliveryMethod);
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
                    //console.log("meeting times:", meetingTimes);
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
                    //console.log("meeting times:", meetingTimes);
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
              /*
              if (course.has_ichair) {
                course.ichair.meeting_times_detail.forEach( mtd => {
                  if (mtd.room === null) {
                    mtd.room = {
                      id: NO_ROOM_SELECTED_ID,
                      short_name: "-----",
                      capacity: -1
                    };
                  }
                });
              }
              if (course.has_banner) {
                course.banner.meeting_times_detail.forEach( mtd => {
                  if (mtd.room === null) {
                    mtd.room = {
                      id: NO_ROOM_SELECTED_ID,
                      short_name: "-----",
                      capacity: -1
                    };
                  }
                });
              }
              */
              _this.courseOfferings.push({
                semester: course.semester,
                semesterId: course.semester_id,
                courseOwnedByUser: course.course_owned_by_user,
                termCode: course.term_code,
                allowRoomRequests: course.allow_room_requests,// whether room edit requests may be made for this semester (regardless of whether the user wants to do them)
                includeRoomComparisons: course.include_room_comparisons,// whether to include room comparisons as part of the meeting time comparisons
                course: course.course,
                creditHours: course.credit_hours,
                name: course.course_title,
                crn: course.crn,
                schedulesMatch: course.schedules_match,
                instructorsMatch: course.instructors_match,
                semesterFractionsMatch: course.semester_fractions_match,
                enrollmentCapsMatch: course.enrollment_caps_match,
                deliveryMethodsMatch: course.delivery_methods_match,
                publicCommentsMatch: course.public_comments_match,
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
                showAllIChairComments: false, //used to toggle between showing all comments and showing an abbreviation
                showAllBannerComments: false, //used to toggle between showing all comments and showing an abbreviation
                banner: course.banner,
                hasIChair: course.has_ichair,
                hasBanner: course.has_banner,
                linked: course.linked,
                allOK: course.all_OK,
                index: course.index, // used as an item-key in the table
                errorMessage: "",
                loadsAdjustedWarning: "",
                classroomsUnassignedWarning: "",
                numberPrimaryInstructorsIncorrectMessage: "" // used to display a message saying that the number of primary instructors is incorrect
              });
            });
            _this.semesterFractionsReverse =
              incomingData.semester_fractions_reverse;
            _this.semesterFractions = incomingData.semester_fractions;
            _this.courseOfferingAlignmentPhaseReady = true;
            console.log("course offering data: ", _this.courseOfferings);
          }
        });
      }
    },
    deactivateScheduleRightArrow(item) {
      if (item.delta !== null) {
        if (
          item.delta.requested_action === DELTA_ACTION_CREATE &&
          !item.delta.request_update_meeting_times
        ) {
          return false;
          /*
          if (item.hasIChair) {// it must have iChair, since the delta object is of type CREATE at this point...but just in case....
            return item.ichair.meeting_times.length === 0;// deactivates if there are no iChair meeting times, since then it agrees with Banner...which currently has nothing
          } else {
            return true;
          }
          */
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
    deactivateMaxEnrollmentRightArrow(item) {
      if (item.delta !== null) {
        if (
          item.delta.requested_action === DELTA_ACTION_CREATE &&
          !item.delta.request_update_max_enrollment
        ) {
          return false;
        }
      }
      return item.enrollmentCapsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateMaxEnrollmentLeftArrow(item) {
      return item.enrollmentCapsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateDeliveryMethodRightArrow(item) {
      if (item.delta !== null) {
        if (
          item.delta.requested_action === DELTA_ACTION_CREATE &&
          !item.delta.request_update_delivery_method
        ) {
          return false;
        }
      }
      return item.deliveryMethodsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateDeliveryMethodLeftArrow(item) {
      return item.deliveryMethodsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateSemesterFractionRightArrow(item) {
      if (item.delta !== null) {
        if (
          item.delta.requested_action === DELTA_ACTION_CREATE &&
          !item.delta.request_update_semester_fraction
        ) {
          return false;
        }
      }
      return item.semesterFractionsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateSemesterFractionLeftArrow(item) {
      return item.semesterFractionsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivatePublicCommentsRightArrow(item) {
      if (item.delta !== null) {
        if (
          item.delta.requested_action === DELTA_ACTION_CREATE &&
          !item.delta.request_update_public_comments
        ) {
          return false;
        }
      }
      return item.publicCommentsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivatePublicCommentsLeftArrow(item) {
      return item.publicCommentsMatch || !item.hasIChair || !item.hasBanner;
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
            semesterFraction: false,
            publicComments: false,
            deliveryMethod: false,
          }, // request all delta mods by default when issuing a "create" request to the registrar
          deltaId: null, // shouldn't exist at this point, since we are creating a new delta object
          action: DELTA_ACTION_DELETE,
          crn: item.crn, // asking the registrar to delete this CRN
          iChairCourseOfferingId: null, // don't have one; we're asking the registrar to delete a course offering b/c it doesn't correspond to one in iChair
          bannerCourseOfferingId: item.banner.course_offering_id, // this is the banner course offering that we are requesting be deleted
          semesterId: item.semesterId,
          includeRoomComparisons: item.includeRoomComparisons
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
            /*
            item.ichair.meeting_times_detail.forEach( mtd => {
              if (mtd.room === null) {
                mtd.room = {
                  id: NO_ROOM_SELECTED_ID,
                  short_name: "-----",
                  capacity: -1
                };
              }
            });
            */
          }
        });
        // add the banner title to the iChair version of the course;
        // the api endpoint checks to see if the banner title already exists,
        // and doesn't add it again if it does, so there's no harm in just 
        // adding it here
        console.log('updating banner title....');
        this.addBannerTitle(item.ichair.course_id, item.banner.course_title);
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
          semesterId: item.semesterId,
          includeRoomComparisons: item.includeRoomComparisons
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
            console.log("in response: ", jsonResponse);
            if (!jsonResponse.number_ichair_primary_instructors_OK) {
              item.numberPrimaryInstructorsIncorrectMessage = "There should be one primary instructor for this course offering in iChair.  Please fix this before requesting an instructor update from the registrar.";
            }
            item.delta = jsonResponse.delta;
            item.enrollmentCapsMatch =
              jsonResponse.agreement_update.max_enrollments_match ||
              item.delta.request_update_max_enrollment;
            item.deliveryMethodsMatch =
              jsonResponse.agreement_update.delivery_methods_match ||
              item.delta.request_update_delivery_method;
            item.publicCommentsMatch =
              jsonResponse.agreement_update.public_comments_match ||
              item.delta.request_update_public_comments;
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
              item.semesterFractionsMatch &&
              item.publicCommentsMatch &&
              item.deliveryMethodsMatch;
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

    addBannerTitle(ichairCourseId, bannerTitle) {
      // add a banner title to an iChair course; the server will check if the banner title is redundant and, if so, will not add it
      let dataForPost = {
        create: [],
        update: [{
          ichair_course_id: ichairCourseId,
          banner_title: bannerTitle
        }]
      };
      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/create-update-courses/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(jsonResponse) {
          console.log("response: ", jsonResponse);
          if (!(jsonResponse.updates_successful && jsonResponse.creates_successful)) {
            console.log('the update to the banner title was not successful....');
          } else {
            console.log('successfully added the banner title to the course!');
          }
        },
        error: function(jqXHR, exception) {
          // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
          console.log(jqXHR);
          //_this.showCreateUpdateErrorMessage();
          //_this.meetingFormErrorMessage =
          //  "Sorry, there appears to have been an error.";
        }
      });
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
          let uniqueChoiceExists = false;
          let course = null;
          if (courseList.length === 1) {
            course = courseList[0];
            if (
              // https://www.w3schools.com/jsref/jsref_includes_array.asp
              courseProperties.title === course.title ||
              course.banner_titles.includes(courseProperties.title)
            ) {
              // we have found the unique course in the iChair database that corresponds to this banner course offering;
              // now create the course offering
              uniqueChoiceExists = true;
            }
          }
          if (uniqueChoiceExists) {
            _this.createNewCourseOffering(item, course.id);
          } else if (courseList.length === 0) {
            // there are no matches for the course in the iChair database, so go ahead and create a new one
            console.log(
              "no match for this course; creating a new one before creating the course offering...."
            );
            _this.createNewCourse(item);
          } else {
            // there are either zero or more than one option (or only one option, but it's not a perfect match....) that exist in the iChair database for the course offering that
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
                // https://www.w3schools.com/jsref/jsref_includes_array.asp
                courseProperties.title === courseOption.title ||
                courseOption.banner_titles.includes(courseProperties.title)
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
              " (" + "CRN: " + item.crn + "; " +
              item.creditHours +
              creditText;
            // https://scotch.io/bar-talk/copying-objects-in-javascript
            // using this approach to make the copy so that we don't risk problems later when we set it back to null
            _this.newCourseOfferingDialogItem = JSON.parse(JSON.stringify(item));
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

    roomListItem(roomList, index) {
      return roomList[index];
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
        this.cancelCourseOfferingDialog();
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
      console.log('Creating a new course before creating the course offering');
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
              console.log('course created successfully; moving on to create the course offering');
              _this.createNewCourseOffering(
                item,
                jsonResponse.created_course_ids[0]
              );
            } else {
              console.log(
                "there were more or fewer than one course created! course id(s): ",
                jsonResponse.created_course_ids
              );
              _this.addGenericServerErrorMessage(item);
            }
          }
        },
        error: function(jqXHR, exception) {
          // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
          console.log(jqXHR);
          _this.showCreateUpdateErrorMessage();
          _this.addGenericServerErrorMessage(item);
          //_this.meetingFormErrorMessage =
          //  "Sorry, there appears to have been an error.";
        }
      });
    },

    addGenericServerErrorMessage(item) {
      this.courseOfferings.forEach(courseOfferingItem => {
        if (item.index === courseOfferingItem.index) {
          courseOfferingItem.errorMessage = "Sorry, there appears to have been an error.  If the problem persists, please contact the iChair administrator.";
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
        deliveryMethod: item.banner.delivery_method,
        includeRoomComparisons: item.includeRoomComparisons,
        semesterId: item.semesterId,
        crn: item.crn,
        loadAvailable: item.creditHours, //need to warn the user that this has been set automatically
        meetings: [],
        instructorDetails: [],
        comments: item.banner.comments
      }
      item.banner.meeting_times_detail.forEach(meetingTime => {
        dataForPost.meetings.push({
          beginAt: meetingTime.begin_at,
          endAt: meetingTime.end_at,
          day: meetingTime.day,
          //room: JSON.parse(JSON.stringify(meetingTime.room))
          rooms: JSON.parse(JSON.stringify(meetingTime.rooms))
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
              /*
              courseOfferingItem.ichair.meeting_times_detail.forEach( mtd => {
                if (mtd.room === null) {
                  mtd.room = {
                    id: NO_ROOM_SELECTED_ID,
                    short_name: "-----",
                    capacity: -1
                  };
                }
              });
              */
              courseOfferingItem.enrollmentCapsMatch = jsonResponse.agreement_update.max_enrollments_match;
              courseOfferingItem.deliveryMethodsMatch = jsonResponse.agreement_update.delivery_methods_match;
              courseOfferingItem.publicCommentsMatch = jsonResponse.agreement_update.public_comments_match;
              courseOfferingItem.instructorsMatch = jsonResponse.agreement_update.instructors_match;
              courseOfferingItem.schedulesMatch = jsonResponse.agreement_update.meeting_times_match;
              courseOfferingItem.semesterFractionsMatch = jsonResponse.agreement_update.semester_fractions_match;
              courseOfferingItem.allOK =
                courseOfferingItem.enrollmentCapsMatch &&
                courseOfferingItem.instructorsMatch &&
                courseOfferingItem.schedulesMatch &&
                courseOfferingItem.semesterFractionsMatch &&
                courseOfferingItem.publicCommentsMatch &&
                courseOfferingItem.deliveryMethodsMatch;
              courseOfferingItem.hasIChair = true;
              courseOfferingItem.linked = true;
              courseOfferingItem.showCourseOfferingRadioSelect = false;
              if (jsonResponse.instructors_created_successfully === false) {
                console.log("error copying instructors!");
                courseOfferingItem.errorMessage =
                  "An error occurred while trying to copy instructor data from the registrar's database.  This can happen if one of the iChair instructors does not exist in the Registrar's database or is no longer 'active' in iChair.";
              } else {
                courseOfferingItem.errorMessage = '';
              }
              if (jsonResponse.load_manipulation_performed === true) {
                console.log("loads were adjusted!");
                courseOfferingItem.loadsAdjustedWarning =
                  "One or more loads were adjusted automatically in the process of copying instructors from the registrar's database.  You may wish to check that this was done correctly.";
              } else {
                courseOfferingItem.loadsAdjustedWarning = '';
              }
              if (jsonResponse.classrooms_unassigned === true) {
                console.log("schedules assigned without classrooms!");
                courseOfferingItem.classroomsUnassignedWarning =
                  "One or more meeting times were scheduled within iChair, but without rooms being assigned.  If you know the appropriate room(s), you may wish to correct this.";
              } else {
                courseOfferingItem.classroomsUnassignedWarning = '';
              }
              // now add the banner title to the course, in case that banner title is not yet associated with that course
              _this.addBannerTitle(courseOfferingItem.ichair.course_id, courseOfferingItem.banner.course_title);
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
            semesterFraction: true,
            publicComments: true,
            deliveryMethod: true,
          }, // request all delta mods by default when issuing a "create" request to the registrar
          deltaId: null, // shouldn't exist at this point, since we have only just linked the Banner course offering with the iChair one
          action: DELTA_ACTION_CREATE,
          crn: null, // doesn't exist yet
          iChairCourseOfferingId: item.ichair.course_offering_id,
          bannerCourseOfferingId: null, // don't have one, since we're requesting that the registrar create one
          semesterId: item.semesterId,
          includeRoomComparisons: item.includeRoomComparisons
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
        // now add the banner title to the iChair course for future reference....
        this.addBannerTitle(item.ichair.course_id, item.banner.course_title);
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
          semesterId: item.semesterId,
          includeRoomComparisons: item.includeRoomComparisons
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
          console.log("back in response: ", jsonResponse);
          if (!jsonResponse.number_ichair_primary_instructors_OK) {
            item.numberPrimaryInstructorsIncorrectMessage = "There should be one primary instructor for this course offering in iChair.  Please fix this before requesting an instructor update from the registrar.";
          }
          item.delta = jsonResponse.delta;
          item.enrollmentCapsMatch =
            jsonResponse.agreement_update.max_enrollments_match ||
            item.delta.request_update_max_enrollment;
          item.deliveryMethodsMatch =
            jsonResponse.agreement_update.delivery_methods_match ||
            item.delta.request_update_delivery_method;
          item.publicCommentsMatch =
            jsonResponse.agreement_update.public_comments_match ||
            item.delta.request_update_public_comments;
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
            item.semesterFractionsMatch &&
            item.publicCommentsMatch &&
            item.deliveryMethodsMatch;
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
      console.log('course info: ', courseInfo);
      let bannerId = null;
      if (courseInfo.hasBanner) {
        bannerId = courseInfo.banner.course_offering_id;
      }
      this.editCourseOfferingData = {
        courseOfferingIndex: courseInfo.index,//useful for fetching the course offering item back later on, in order to make changes
        courseOfferingId: courseInfo.ichair.course_offering_id,
        ichairObject: courseInfo.ichair,
        bannerId: bannerId,
        delta: courseInfo.delta,
        includeRoomComparisons: courseInfo.includeRoomComparisons
      };
      this.dialogTitle = courseInfo.course + ": " + courseInfo.name;
      let meetingDetails = courseInfo.ichair.meeting_times_detail;
      this.dialog = true;
      //trick to clone the object: https://www.codementor.io/junedlanja/copy-javascript-object-right-way-ohppc777d
      this.editMeetings = JSON.parse(JSON.stringify(meetingDetails));
      this.editMeetings.forEach(meeting => {
        meeting.delete = false;
        // looks like the trick of using JSON.parse(JSON.stringify(...)) to clone an object has a problem when
        // a number is Number.NEGATIVE_INFINITY...it appears to turn it into null, so we need to replace the null by 
        // Number.NEGATIVE_INFINITY again.
        /*
        if (meeting.room.id === null) {
          meeting.room.id = NO_ROOM_SELECTED_ID;
        }
        */
        if (meeting.rooms.length === 0) {
          meeting.rooms.push({
            id: NO_ROOM_SELECTED_ID,
            short_name: "",
            capacity: -1
          });
        }
        // the id property can be edited in the dialog...and will get out of synch with the short_name and capacity, so those are
        // being altered here.  There must be a better way to do this, but vue wants to set the v-model to a property of an object
        // that is being iterated over....  In any case, we will only use the id later on.
        meeting.rooms.forEach( room => {
          room.short_name = "";
          room.capacity = -1; 
        })
      });
      if (courseInfo.ichair.delivery_method.id === null) {
        this.editDeliveryMethodId = NO_ROOM_SELECTED_ID;
      } else {
        this.editDeliveryMethodId = courseInfo.ichair.delivery_method.id;
      }
      console.log('edit meetings: ', this.editMeetings);
      this.editEnrollmentCap = courseInfo.ichair.max_enrollment;
      this.editSemesterFraction = courseInfo.ichair.semester_fraction;
      this.initialMeetingData = meetingDetails;
      this.initialEnrollmentData = this.editEnrollmentCap;
      this.initialSemesterFractionData = this.editSemesterFraction;
      this.initialDeliveryMethodId = this.editDeliveryMethodId;
    },

    editOfferingInstructors(courseInfo) {
      let bannerId = null;
      if (courseInfo.hasBanner) {
        bannerId = courseInfo.banner.course_offering_id;
      }
      this.editCourseOfferingData = {
        courseOfferingIndex: courseInfo.index,//useful for fetching the course offering item back later on, in order to make changes
        courseOfferingId: courseInfo.ichair.course_offering_id,
        ichairObject: courseInfo.ichair,
        bannerId: bannerId,
        delta: courseInfo.delta,
        includeRoomComparisons: courseInfo.includeRoomComparisons
      };
      this.facultyChoices = courseInfo.ichair.available_instructors; // set the faculty choices for the drop-down for this course offering
      console.log('initializing dialog; faculty choices: ', this.facultyChoices);
      console.log('course info: ', courseInfo);
      this.dialogTitle = courseInfo.course + ": " + courseInfo.name;
      this.editLoadAvailable = courseInfo.ichair.load_available;
      this.initialLoadAvailableData = this.editLoadAvailable;
      let instructorDetails = courseInfo.ichair.instructors_detail;
      this.editInstructors = JSON.parse(JSON.stringify(instructorDetails));
      console.log('edit instructors: ', this.editInstructors);
      let index = 0;
      this.editInstructors.forEach(instructor => {
        instructor.index = index;
        instructor.delete = false;
        instructor.is_primary_disabled = (this.editInstructors.length === 1) && instructor.is_primary;
        index += 1;
      });
      this.editInstructorsDialog = true;
    },

    addInstructor() {
      console.log('got here!');
      maxIndex = -Infinity;
      this.editInstructors.forEach(instructor => {
        if (instructor.index > maxIndex) {
          maxIndex = instructor.index;
        }
      });
      this.editInstructors.push({
        delete: false,
        id: null,
        name: "",
        is_primary: false,
        is_primary_disabled: false,
        index: maxIndex + 1,
        load_credit: 0
      });
      this.editInstructors.forEach(instructor => {
        instructor.is_primary_disabled = false;
      })
    },

    onIsPrimaryChanged(instructor) {
      console.log('instructor: ', instructor);
      if (instructor.is_primary) {
        // this instructor has just been named the primary instructor, so set the is_primary setting for all other instructors to false
        this.editInstructors.forEach(instructorInList => {
          if (instructorInList.index !== instructor.index) {
            instructorInList.is_primary = false;
          }
        });
      }
    },

    cancelInstructorsForm() {
      this.editInstructorsDialog = false;
      this.editInstructors = [];
      this.instructorFormErrorMessage = "";
      this.editLoadAvailable = null;
      this.initialLoadAvailableData = null;
      this.editCourseOfferingData = {};
      this.facultyChoices = [];
      console.log('faculty choices: ', this.facultyChoices);
    },

    submitInstructorsForm(courseInfo) {
      // form validation is a bit messy here because of all the edge cases...!      
      this.instructorFormErrorMessage = "";
      let instructorList = [];
      console.log('submit!');
      let errorInForm = false;
      let numPrimaryInstructors = 0;
      let numInstructors = 0;

      let loadAvailable = +this.editLoadAvailable;
      if (Number.isNaN(loadAvailable)) {
        console.log('not a number!');
        this.instructorFormErrorMessage = "The total number of load hours available must be a number greater than or equal to zero.";
        errorInForm = true;
      } else if (loadAvailable < 0) {// at this point it is presumably a number....
        console.log('negative!');
        this.instructorFormErrorMessage = "The total number of load hours available must be a number greater than or equal to zero.";
        errorInForm = true;
      }

      this.editInstructors.forEach(instructor => {
        if (instructor.is_primary && (!this.instructorToBeDeleted(instructor))) {
          numPrimaryInstructors += 1;
        }
        if (!this.instructorToBeDeleted(instructor)) {
          numInstructors += 1;
        }
      });
      if ((numInstructors > 0) && (numPrimaryInstructors !== 1)) {
        this.instructorFormErrorMessage = "Please choose a primary instructor.";
        errorInForm = true;
      }
      if (!errorInForm) {
        this.editInstructors.forEach(instructor => {
          console.log('type of initial load credit: ', typeof instructor.load_credit);
          let loadCredit = +instructor.load_credit;
          // https://www.w3schools.com/jsref/jsref_isnan.asp
          if (Number.isNaN(loadCredit)) {
            this.instructorFormErrorMessage = "The number of load hours must be a number.";
            errorInForm = true;
          }
          console.log('got here!');
          if ((!errorInForm) && (!this.instructorToBeDeleted(instructor))) {
            if (instructor.id === null) {
              errorInForm = true;
              this.instructorFormErrorMessage = "Please choose an instructor for each entry.";
            } else if (loadCredit < 0) {
              errorInForm = true;
              this.instructorFormErrorMessage = "The number of load hours for each instructor must be greater than or equal to zero.";
            }
            if ((!errorInForm) && (!this.instructorToBeDeleted(instructor))) {
              instructorList.forEach(instructoryInList => {
                // make sure they're both numbers....
                let instructorId = +instructor.id;
                let instructorInListId = +instructoryInList.id;
                if (instructorId === instructorInListId) {
                  errorInForm = true;
                  this.instructorFormErrorMessage = "Please choose each instructor at most once.";
                }
              });
              if (!errorInForm) {
                instructorList.push({
                  id: +instructor.id,
                  loadCredit: loadCredit,
                  isPrimary: instructor.is_primary
                });
              }
            }
          }
        });
      }

      if (!errorInForm) {
        console.log('ready to submit! ', instructorList);
        
        let dataForPost = {
          courseOfferingId: this.editCourseOfferingData.courseOfferingId,
          snapshot: this.editCourseOfferingData.ichairObject.snapshot,
          hasBanner: this.editCourseOfferingData.bannerId !== null,// safer to interpret the null here than in the python code, where it will probably be converted to None(?)
          bannerId: this.editCourseOfferingData.bannerId, // in python code -- first check if hasBanner; if so, can safely get id
          hasDelta: this.editCourseOfferingData.delta !== null,// same idea as above....
          delta: this.editCourseOfferingData.delta,
          instructorList: instructorList,
          loadAvailable: loadAvailable,
          includeRoomComparisons: this.editCourseOfferingData.includeRoomComparisons,
          loadAvailableRequiresUpdate: !(loadAvailable === this.initialLoadAvailableData),
        };
        console.log('data for post: ', dataForPost);
        let _this = this;
        $.ajax({
          // initialize an AJAX request
          type: "POST",
          url: "/planner/ajax/update-instructors-for-course-offering/",
          dataType: "json",
          data: JSON.stringify(dataForPost),
          success: function(jsonResponse) {
            console.log("response: ", jsonResponse);
            _this.courseOfferings.forEach(courseOfferingItem => {
              if (_this.editCourseOfferingData.courseOfferingIndex === courseOfferingItem.index) {
                if (jsonResponse.has_delta) {
                  courseOfferingItem.delta = jsonResponse.delta;
                } else {
                  courseOfferingItem.delta = null;
                }
                courseOfferingItem.ichair.snapshot = jsonResponse.snapshot;
                courseOfferingItem.ichair.change_can_be_undone.instructors = true;
                courseOfferingItem.ichair.load_available = jsonResponse.load_available;
                courseOfferingItem.ichair.instructors = jsonResponse.instructors;
                courseOfferingItem.ichair.instructors_detail = jsonResponse.instructors_detail;
                if (jsonResponse.has_delta) {
                  courseOfferingItem.instructorsMatch = jsonResponse.instructors_match || jsonResponse.delta.request_update_instructors;
                } else {
                  courseOfferingItem.instructorsMatch = jsonResponse.instructors_match;
                }
                courseOfferingItem.allOK =
                  courseOfferingItem.enrollmentCapsMatch &&
                  courseOfferingItem.instructorsMatch &&
                  courseOfferingItem.schedulesMatch &&
                  courseOfferingItem.semesterFractionsMatch &&
                  courseOfferingItem.publicCommentsMatch && 
                  courseOfferingItem.deliveryMethodsMatch;
                courseOfferingItem.numberPrimaryInstructorsIncorrectMessage = "";
                courseOfferingItem.loadsAdjustedWarning = "";
                courseOfferingItem.errorMessage = ""; // clear out any error that may have been there, since things are probably OK now....and if not, the user will see an error in the dialog
              }
            });

            if (!jsonResponse.updates_completed) {
              _this.instructorFormErrorMessage = "Sorry, there appears to have been a problem with performing the requested update(s).";
            } else {
              _this.cancelInstructorsForm();
            }
            
            
            //_this.cancelCommentsForm();
            //console.log('course offerings: ', _this.courseOfferings);
          },
          error: function(jqXHR, exception) {
            // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
            console.log(jqXHR);
            //_this.showCreateUpdateErrorMessage();
            _this.instructorFormErrorMessage = "Sorry, there appears to have been an error.";
          }
        });
      }
      //this.cancelInstructorsForm();
    },

    instructorToBeDeleted(instructor) {
      let loadCredit = +instructor.load_credit;
      return instructor.delete || ((instructor.id === null) && (loadCredit === 0) && (!instructor.is_primary));
    },

    displayAddNoteButton(courseInfo) {
      // returns true or false, depending on whether one can add a note for the registrar for this course offering
      // conditions:
      //  - if a delta object already exists, but there is not yet a comment, then true
      //  - if no delta object exists yet:
      //    - if only have a course offering in iChair, then false (user needs to request that the Banner create a course offering first)
      //    - if only have a course offering in Banner, then false (user should request a "delete" or should copy the course offering over to iChair first)
      //    - if the course offering exists in iChair and in Banner, then true (and if the button is clicked, create a delta of "update" type)
      if (courseInfo.delta !== null) {
        // a delta object exists
        return !courseInfo.delta.registrar_comment_exists;
      } else {
        return courseInfo.hasIChair && courseInfo.hasBanner;
      }
    },

    displayNote(courseInfo) {
      // whether or not to display a note for the registrar for this course offering
      if (courseInfo.delta !== null) {
        // a delta object exists
        return courseInfo.delta.registrar_comment_exists;
      } else {
        return false;
      }
    },

    displayNoteForRegistrarDialog(courseInfo) {
      console.log('display note!');
      let bannerId = null;
      let iChairId = null;
      if (courseInfo.hasBanner) {
        bannerId = courseInfo.banner.course_offering_id;
      }
      if (courseInfo.hasIChair) {
        iChairId = courseInfo.ichair.course_offering_id;
      }
      if (courseInfo.delta !== null) {
        if (courseInfo.delta.registrar_comment_exists) {
          this.commentForRegistrar = courseInfo.delta.registrar_comment;
        } else {
          this.commentForRegistrar = "";
        }
      } else {
        this.commentForRegistrar = "";
      }
      this.editCourseOfferingData = {
        courseOfferingIndex: courseInfo.index,//useful for fetching the course offering item back later on, in order to make changes
        courseOfferingId: iChairId,
        ichairObject: courseInfo.ichair,
        bannerId: bannerId,
        iChairId: iChairId,
        delta: courseInfo.delta,
        hasIChair: courseInfo.hasIChair,
        hasBanner: courseInfo.hasBanner,
        includeRoomComparisons: courseInfo.includeRoomComparisons
      };
      this.dialogTitle = courseInfo.course + ": " + courseInfo.name;
      this.commentForRegistrarDialog = true;
    },

    deleteNoteForRegistrar(courseInfo) {
      // used for deleting a note for the registrar on an existing delta object
      console.log('delete the note!');
      this.editCourseOfferingData = {
        courseOfferingIndex: courseInfo.index,//useful for fetching the course offering item back later on, in order to make changes
      };
      let noteInfo = {
        deltaId: courseInfo.delta.id,
        hasDelta: true,
        action: 'delete',
        text: null, // unimportant, since the note is going to be deleted anyways
        iChairId: courseInfo.hasIChair ? courseInfo.ichair.course_offering_id : null,
        bannerId: courseInfo.hasBanner ? courseInfo.banner.course_offering_id : null,
        hasIChair: courseInfo.hasIChair, // but doesn't matter
        hasBanner: courseInfo.hasBanner, // but doesn't matter
        includeRoomComparisons: courseInfo.includeRoomComparisons
      }
      this.createUpdateDeleteNoteForRegistrar(noteInfo);
    },

    noteForRegistrarTooLong() {
      return this.commentForRegistrar.length > 500;
    },

    cancelNoteForRegistrarForm() {
      console.log('cancel note for registrar dialog');
      this.editCourseOfferingData = {};
      this.dialogTitle = "";
      this.commentForRegistrarDialog = false;
      this.commentForRegistrar = "";
    },
    submitNoteForRegistrar() {
      // either submitting a new note or updating an existing one; if the user cleared a note by backspacing, may need to delete a note....
      console.log('submit note for registrar');
      let OKToSubmit = true;
      let hasDelta = !(this.editCourseOfferingData.delta === null);
      let deltaId = null;
      if (hasDelta) {
        deltaId = this.editCourseOfferingData.delta.id;
      }
      let text = this.commentForRegistrar;
      if (text === "") {// user wants to delete the note....
        if (hasDelta) {
          action = 'delete'; // delete the note, not the delta object itself....
        } else {
          OKToSubmit = false;
          this.cancelNoteForRegistrarForm();
        }
      } else { // text is not a blank string
        if (hasDelta) {
          action = 'update'; // a delta object already exists, so we're doing an update to the delta object
        } else {
          action = 'create'; // no delta object, so need to create one (which will, confusingly, be of the "update" type....)
        }
      }
      let noteInfo = {
        deltaId: deltaId,
        hasDelta: hasDelta,
        action: action,
        text: text,
        iChairId: this.editCourseOfferingData.iChairId,
        bannerId: this.editCourseOfferingData.bannerId,
        hasIChair: this.editCourseOfferingData.hasIChair,
        hasBanner: this.editCourseOfferingData.hasBanner,
        includeRoomComparisons: this.editCourseOfferingData.includeRoomComparisons
      }
      if (OKToSubmit) {
        this.createUpdateDeleteNoteForRegistrar(noteInfo);
      }
    },

    createUpdateDeleteNoteForRegistrar(noteInfo) {
      console.log('note info: ', noteInfo);
      var _this = this;
      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/create-update-delete-note-for-registrar/",
        dataType: "json",
        data: JSON.stringify(noteInfo),
        success: function(jsonResponse) {
          console.log("response: ", jsonResponse);
          _this.courseOfferings.forEach(courseOfferingItem => {
            if (_this.editCourseOfferingData.courseOfferingIndex === courseOfferingItem.index) {
              courseOfferingItem.delta = jsonResponse.delta_response;
            }
          });
          _this.cancelNoteForRegistrarForm();
          //console.log('course offerings: ', _this.courseOfferings);
        },
        error: function(jqXHR, exception) {
          // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
          console.log(jqXHR);
          //_this.showCreateUpdateErrorMessage();
          _this.commentFormErrorMessage = "Sorry, there appears to have been an error.";
        }
      });
      


    },

    editPublicComments(courseInfo) {
      this.dialogTitle = "Public Comments for " + courseInfo.course + ": " + courseInfo.name;
      let bannerId = null;
      if (courseInfo.hasBanner) {
        bannerId = courseInfo.banner.course_offering_id;
      }
      this.editCourseOfferingData = {
        courseOfferingIndex: courseInfo.index,//useful for fetching the course offering item back later on, in order to make changes
        courseOfferingId: courseInfo.ichair.course_offering_id,
        ichairObject: courseInfo.ichair,
        bannerId: bannerId,
        delta: courseInfo.delta,
        includeRoomComparisons: courseInfo.includeRoomComparisons
      };
      let commentDetails = courseInfo.ichair.comments.comment_list;
      this.publicCommentsDialog = true;
      //trick to clone the object: https://www.codementor.io/junedlanja/copy-javascript-object-right-way-ohppc777d
      this.editComments = JSON.parse(JSON.stringify(commentDetails));
      this.editComments.forEach(comment => {
        comment.delete = false;
        if ((typeof comment.sequence_number) === 'string') {
          console.log('comment is a string!  fixing....');
          // https://gomakethings.com/converting-strings-to-numbers-with-vanilla-javascript/
          comment.sequence_number = Number(comment.sequence_number);
        }
      });
      this.initialCommentData = commentDetails;
      if (this.editComments.length === 0) {
        this.addComment();
      }
    },
    commentsTooLong() {
      let commentsAreLong = false;
      this.editComments.forEach(comment => {
        if ( comment.text.length>60 ) {
          commentsAreLong = true;
        }
      });
      return commentsAreLong;
    },
    addComment() {
      let maxSequenceNumber = -Infinity;
      this.editComments.forEach(comment => {
        if (comment.sequence_number > maxSequenceNumber) {
          maxSequenceNumber = comment.sequence_number;
        }
      });
      if (maxSequenceNumber === -Infinity) {
        maxSequenceNumber = 1;
      }
      this.editComments.push({
        delete: false,
        text: "",
        sequence_number: maxSequenceNumber + 1,
        id: null
      });
      console.log('comment data: ', this.editComments);
    },
    cancelCommentsForm() {
      this.publicCommentsDialog = false;
      this.dialogTitle = "";
      this.editComments = [];
    },
    showLessOfIChairComments(courseInfo) {
      courseInfo.showAllIChairComments = false;
    },
    showMoreOfIChairComments(courseInfo) {
      courseInfo.showAllIChairComments = true;
    },
    showLessOfBannerComments(courseInfo) {
      courseInfo.showAllBannerComments = false;
    },
    showMoreOfBannerComments(courseInfo) {
      courseInfo.showAllBannerComments = true;
    },
    submitComments() {
      console.log("submit comments!");
      let commentsToDelete = []; //list of ids
      let commentsToUpdate = []; //list of objects
      let commentsToCreate = []; //list of objects
      let commentsToLeave = []; //list of objects
      this.commentFormErrorMessage = "";
      //let formOK = true;
      // {'id': 20, 'text': 'Coreq MAT 151: designed to help', 'sequence_number': 1, 'delete': False}
      this.editComments.forEach(comment => {
        if (comment.id !== null && comment.delete === true) {
          commentsToDelete.push(comment.id);
        } else if (comment.delete === false) {
          // check if need to make updates....
          // if the id is null, check if there is any text; if so, create a new comment
          // if the id is not null, check if there has been a change; if so, do an update (but only if there is some text -- otherwise do a delete)
          if (comment.id === null) {
            if (comment.text !== '') {
              commentsToCreate.push({
                sequence_number: comment.sequence_number,
                text: comment.text
              });
            }
          } else { //comment.id is not null, so check if should do an update, or possibly a delete
            let foundComment = false;
            let matchingComment = null;
            let commentsIdentical = true;
            this.initialCommentData.forEach(initialData => {
              if (initialData.id === comment.id) {
                foundComment = true;
                matchingComment = initialData;
              }
            });
            if (foundComment) {
              commentsIdentical = matchingComment.text === comment.text;
            } else {
              console.log(
                "something is wrong! cannot find the id for the update...."
              );
            }
            if (commentsIdentical) {
              commentsToLeave.push({
                sequence_number: comment.sequence_number,
                text: comment.text
              });
            } else if (comment.text === '') {// user erased the comment, presumably meaning to delete it
              commentsToDelete.push(comment.id);
            } else {
              commentsToUpdate.push({
                id: comment.id,
                sequence_number: comment.sequence_number,
                text: comment.text
              });
            }
          }
        }
      });
      let numChanges =
        commentsToCreate.length +
        commentsToUpdate.length +
        commentsToDelete.length;
      if (numChanges > 0) {
        // now post the data...
        var _this = this;
        let dataForPost = {
          courseOfferingId: this.editCourseOfferingData.courseOfferingId,
          snapshot: this.editCourseOfferingData.ichairObject.snapshot,
          hasBanner: this.editCourseOfferingData.bannerId !== null,// safer to interpret the null here than in the python code, where it will probably be converted to None(?)
          bannerId: this.editCourseOfferingData.bannerId, // in python code -- first check if hasBanner; if so, can safely get id
          hasDelta: this.editCourseOfferingData.delta !== null,// same idea as above....
          delta: this.editCourseOfferingData.delta,
          delete: commentsToDelete,
          update: commentsToUpdate,
          create: commentsToCreate,
          includeRoomComparisons: this.editCourseOfferingData.includeRoomComparisons
        };
        $.ajax({
          // initialize an AJAX request
          type: "POST",
          url: "/planner/ajax/update-public-comments/",
          dataType: "json",
          data: JSON.stringify(dataForPost),
          success: function(jsonResponse) {
            console.log("response: ", jsonResponse);
            _this.courseOfferings.forEach(courseOfferingItem => {
              if (_this.editCourseOfferingData.courseOfferingIndex === courseOfferingItem.index) {
                if (jsonResponse.has_delta) {
                  courseOfferingItem.delta = jsonResponse.delta;
                } else {
                  courseOfferingItem.delta = null;
                }

                courseOfferingItem.ichair.snapshot = jsonResponse.snapshot;
                courseOfferingItem.ichair.change_can_be_undone.public_comments = true;
              
                courseOfferingItem.ichair.comments = jsonResponse.comments;
                if (jsonResponse.has_delta) {
                  courseOfferingItem.publicCommentsMatch = jsonResponse.public_comments_match || jsonResponse.delta.request_update_public_comments;
                } else {
                  courseOfferingItem.publicCommentsMatch = jsonResponse.public_comments_match;
                }
                courseOfferingItem.allOK =
                  courseOfferingItem.enrollmentCapsMatch &&
                  courseOfferingItem.instructorsMatch &&
                  courseOfferingItem.schedulesMatch &&
                  courseOfferingItem.semesterFractionsMatch &&
                  courseOfferingItem.publicCommentsMatch &&
                  courseOfferingItem.deliveryMethodsMatch;
              }
            });
            _this.cancelCommentsForm();
            console.log('course offerings: ', _this.courseOfferings);
          },
          error: function(jqXHR, exception) {
            // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
            console.log(jqXHR);
            //_this.showCreateUpdateErrorMessage();
            _this.commentFormErrorMessage = "Sorry, there appears to have been an error.";
          }
        });
      }
      this.cancelCommentsForm();
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
          item.deliveryMethodsMatch =
            jsonResponse.agreement_update.delivery_methods_match;
          item.publicCommentsMatch =
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
            item.semesterFractionsMatch &&
            item.publicCommentsMatch &&
            item.deliveryMethodsMatch;
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
      //  - DELTA_UPDATE_TYPE_COMMENTS
      //  - DELTA_UPDATE_TYPE_DELIVERY_METHOD
      // updateOrUndo is DELTA_ACTION_UPDATE or DELTA_ACTION_UNDO_UPDATE
      //
      // https://www.w3schools.com/jsref/jsref_switch.asp

      //deltaUpdate(item, DELTA_UPDATE_TYPE_INSTRUCTORS, DELTA_ACTION_SET)
      // 



      let updateTypeOK = true;
      let dataOK = true;
      let deltaMods = {};
      switch (updateType) {
        case DELTA_UPDATE_TYPE_INSTRUCTORS:
          if ( updateSetOrUnset === DELTA_ACTION_SET ) {
            // check if there is more than one primary instructor; if so, notify the user (via a dialog) that this needs to be fixed first
            console.log('number primary instructors is OK: ', this.numberPrimaryInstructorsOK(item));
            if (!this.numberPrimaryInstructorsOK(item)) {
              this.numberPrimaryInstructorsIncorrectDialog = true;
              dataOK = false;
            }
          }
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
        case DELTA_UPDATE_TYPE_DELIVERY_METHOD:
            deltaMods = {
              deliveryMethod: updateSetOrUnset === DELTA_ACTION_SET ? true : false
            };
            break;
        case DELTA_UPDATE_TYPE_COMMENTS:
          deltaMods = {
            publicComments: updateSetOrUnset === DELTA_ACTION_SET ? true : false
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

      if (updateTypeOK && dataOK) {
        console.log("generate delta: ", updateType);
        console.log("item", item);
        this.generateUpdateDelta(item, deltaMods);
      }
    },

    numberPrimaryInstructorsOK(item) {
      // This method checks to the iChair instructors for this course offering.  It returns the following:
      // 0 instructors: true (no primary instructors, but that's OK)
      // 1 instructor: true (doesn't matter whether or not the instructor is labelled as primary, since there is only one)
      // >=2 instructors: true if exactly one of them is primary; otherwise false;
      // If the item does not contain an iChair section (which shouldn't happen!), it returns true, thereby failing silently
      console.log(item);
      if (item.hasIChair) {
        let numInstructors = item.ichair.instructors_detail.length;
        let numPrimaryInstructors = 0;
        item.ichair.instructors_detail.forEach(instructor => {
          if (instructor.is_primary === true) {
            numPrimaryInstructors += 1;
          }
        });
        if (numInstructors >= 2) {
          return numPrimaryInstructors === 1;
        } else {
          return true;
        }
      } else {
        return true;
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
            semesterId: item.semesterId,
            includeRoomComparisons: item.includeRoomComparisons
          };
        } else if (item.delta.requested_action === DELTA_ACTION_CREATE) {
          dataForPost = {
            deltaMods: deltaMods,
            deltaId: item.delta.id,
            action: item.delta.requested_action, // action we are requesting of the registrar
            crn: item.crn,
            iChairCourseOfferingId: item.ichair.course_offering_id,
            bannerCourseOfferingId: null, // no banner course offering exists, since we are requesting that the registrar create a new one
            semesterId: item.semesterId,
            includeRoomComparisons: item.includeRoomComparisons
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
          semesterId: item.semesterId,
          includeRoomComparisons: item.includeRoomComparisons
        };
      }

      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/generate-update-delta/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(jsonResponse) {
          console.log("back in response: ", jsonResponse);
          if (!jsonResponse.number_ichair_primary_instructors_OK) {
            item.numberPrimaryInstructorsIncorrectMessage = "There should be one primary instructor for this course offering in iChair.  Please fix this before requesting an instructor update from the registrar.";
          }
          item.delta = jsonResponse.delta;
          item.enrollmentCapsMatch =
            jsonResponse.agreement_update.max_enrollments_match ||
            item.delta.request_update_max_enrollment;
          item.deliveryMethodsMatch =
            jsonResponse.agreement_update.delivery_methods_match ||
            item.delta.request_update_delivery_method;
          item.publicCommentsMatch =
            jsonResponse.agreement_update.public_comments_match ||
            item.delta.request_update_public_comments;
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
            item.semesterFractionsMatch &&
            item.publicCommentsMatch &&
            item.deliveryMethodsMatch;
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

    copyDataToiChair(item, dataToUpdate, copyFromBanner) {
      // assume that an iChair course offering object exists already (the actual creation of an
      // iChair course offering -- i.e., copying the entire course offering from Banner -- already 
      // happens in another method); if copyFromBanner === true, then a banner course offering should exist, 
      // or else we have nothing to copy from....
      console.log("item: ", item);
      console.log("data to update: ", dataToUpdate);
      console.log("copy from Banner? ", copyFromBanner, typeof copyFromBanner);
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
        bannerCourseOfferingId: item.hasBanner ? item.banner.course_offering_id : null,
        hasBanner: item.hasBanner,
        copyFromBanner: copyFromBanner,// true if we are to copy the data from Banner to iChair; false if we are to use the "snapshot" object to perform an "undo" operation
        snapshot: item.ichair.snapshot,
        deltaId: deltaId,
        propertiesToUpdate: [],
        departmentId: json_data.departmentId, // add the faculty id to the GET parameters
        yearId: json_data.yearId,
        includeRoomComparisons: item.includeRoomComparisons
      };
      if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT) {
        dataForPost.propertiesToUpdate.push("max_enrollment");
      } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION) {
        dataForPost.propertiesToUpdate.push("semester_fraction");
      } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS) {
        dataForPost.propertiesToUpdate.push("instructors");
      } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES) {
        dataForPost.propertiesToUpdate.push("meeting_times");
      } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_COMMENTS) {
        dataForPost.propertiesToUpdate.push("comments");
      }
        else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_DELIVERY_METHOD) {
          dataForPost.propertiesToUpdate.push("delivery_method");
      }
      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/copy-course-offering-data-to-ichair/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(jsonResponse) {
          console.log("response!!!: ", jsonResponse);
          let commentsChangeCanBeUndone = false;
          let instructorsChangeCanBeUndone = false;
          let maxEnrollmentChangeCanBeUndone = false;
          let meetingTimesChangeCanBeUndone = false;
          let semesterFractionChangeCanBeUndone = false;
          let deliveryMethodChangeCanBeUndone = false;
          if (item.hasIChair) {
            // get the "change_can_be_undone" settings before making the updates....
            commentsChangeCanBeUndone = item.ichair.change_can_be_undone.comments;
            instructorsChangeCanBeUndone = item.ichair.change_can_be_undone.instructors;
            maxEnrollmentChangeCanBeUndone = item.ichair.change_can_be_undone.max_enrollment;
            meetingTimesChangeCanBeUndone = item.ichair.change_can_be_undone.meeting_times;
            semesterFractionChangeCanBeUndone = item.ichair.change_can_be_undone.semester_fraction;
            deliveryMethodChangeCanBeUndone = item.ichair.change_can_be_undone.delivery_method;
          }

          item.delta = jsonResponse.delta_response;
          item.enrollmentCapsMatch =
            jsonResponse.agreement_update.max_enrollments_match; // don't need to check item.delta.request_update_max_enrollment, since this was already sorted out by the server-side code....
          item.publicCommentsMatch =
            jsonResponse.agreement_update.public_comments_match; // don't need to check item.delta.request_update_max_enrollment, since this was already sorted out by the server-side code....
          item.instructorsMatch =
            jsonResponse.agreement_update.instructors_match;
          item.schedulesMatch =
            jsonResponse.agreement_update.meeting_times_match;
          item.semesterFractionsMatch =
            jsonResponse.agreement_update.semester_fractions_match;
          item.deliveryMethodsMatch =
            jsonResponse.agreement_update.delivery_methods_match;
          item.allOK =
            item.enrollmentCapsMatch &&
            item.instructorsMatch &&
            item.schedulesMatch &&
            item.semesterFractionsMatch &&
            item.publicCommentsMatch &&
            item.deliveryMethodsMatch;
          item.ichair = jsonResponse.course_offering_update;
          /*
          item.ichair.meeting_times_detail.forEach( mtd => {
            if (mtd.room === null) {
              mtd.room = {
                id: NO_ROOM_SELECTED_ID,
                short_name: "-----",
                capacity: -1
              };
            }
          });
          */

          // if changes could previously be undone for some category, add that possibility here...otherwise this gets forgotten for other categories 
          // than the one(s) that were just edited; the following gives the default behaviour....
          item.ichair.change_can_be_undone.comments = item.ichair.change_can_be_undone.comments || commentsChangeCanBeUndone;
          item.ichair.change_can_be_undone.instructors = item.ichair.change_can_be_undone.instructors || instructorsChangeCanBeUndone;
          item.ichair.change_can_be_undone.max_enrollment = item.ichair.change_can_be_undone.max_enrollment || maxEnrollmentChangeCanBeUndone;
          item.ichair.change_can_be_undone.meeting_times = item.ichair.change_can_be_undone.meeting_times || meetingTimesChangeCanBeUndone;
          item.ichair.change_can_be_undone.semester_fraction = item.ichair.change_can_be_undone.semester_fraction || semesterFractionChangeCanBeUndone;
          item.ichair.change_can_be_undone.delivery_method = item.ichair.change_can_be_undone.delivery_method || deliveryMethodChangeCanBeUndone;

          // if we are undoing a previous change, then should set the undo flag back to false....
          if (!copyFromBanner) {
            if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT) {
              item.ichair.change_can_be_undone.max_enrollment = false;
            } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION) {
              item.ichair.change_can_be_undone.semester_fraction = false;
            } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS) {
              item.ichair.change_can_be_undone.instructors = false;
            } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES) {
              item.ichair.change_can_be_undone.meeting_times = false;
            } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_COMMENTS) {
              item.ichair.change_can_be_undone.comments = false;
            } else if (dataToUpdate === COPY_REGISTRAR_TO_ICHAIR_DELIVERY_METHOD) {
              item.ichair.change_can_be_undone.delivery_method = false;
            }
          }

          if (jsonResponse.offering_instructors_copied_successfully === false) {
            console.log("error copying instructors!");
            if (copyFromBanner) {
              item.errorMessage =
                "An error occurred while trying to copy instructor data from the registrar's database.  This can happen if one of the iChair instructors does not exist in the Registrar's database or is no longer 'active' in iChair.";
            } else {
              item.errorMessage =
                "An error occurred while trying to edit instructor data.  This can happen if one of the instructors is no longer 'active' in iChair.";
            }
          } else {
            item.errorMessage = '';
          }
          if (jsonResponse.load_manipulation_performed === true) {
            console.log("loads were adjusted!");
            item.loadsAdjustedWarning =
              "One or more loads were adjusted automatically in the process of copying instructors from the registrar's database.  You may wish to check that this was done correctly.";
          } else {
            item.loadsAdjustedWarning = '';
          }
          if (jsonResponse.classrooms_unassigned === true) {
            console.log("schedules assigned without classrooms!");
            item.classroomsUnassignedWarning =
              "One or more meeting times were scheduled within iChair, but without rooms being assigned.  If you know the appropriate room(s), you may wish to correct this.";
          } else {
            item.classroomsUnassignedWarning = '';
          }
          console.log('item after update: ', item);

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
        id: null,
        room: {
          id: NO_ROOM_SELECTED_ID,
          short_name: "-----",
          capacity: -1
        },
        rooms: [{
          id: NO_ROOM_SELECTED_ID,
          short_name: "-----",
          capacity: -1
        }]
      });
    },
    cancelMeetingsForm() {
      this.dialog = false;
      this.editMeetings = [];
      this.meetingFormErrorMessage = "";
      this.enrollmentErrorMessage = "";
      this.editCourseOfferingData = {};
      this.editEnrollmentCap = null;
      this.editSemesterFraction = null;
      this.editDeliveryMethodId = null;
    },
    submitMeetingsForm() {
      let meetingsToDelete = []; //list of ids
      let meetingsToUpdate = []; //list of objects
      let meetingsToCreate = []; //list of objects
      let meetingsToLeave = []; //list of objects
      this.meetingFormErrorMessage = "";
      let formOK = true;
      updateEnrollmentCap = false;
      updateDeliveryMethod = false;
      updateSemesterFraction = false;
      let numChanges = 0;
      console.log('enrollment cap: ', this.editEnrollmentCap, ' ', typeof this.editEnrollmentCap);
      console.log('sem fraction: ', this.editSemesterFraction, ' ', typeof this.editSemesterFraction);
      console.log('delivery method: ', this.editDeliveryMethodId, ' ', typeof this.editDeliveryMethodId);
      
      // this.editEnrollmentCap could be either an int (the original data) or a string (if it's been edited, I think);
      // the following checks that, no matter if it is a string or an int, it has the form of an int;
      // using this because parseInt() is pretty forgiving.  If the user types in '8a', we probably don't want to accept that!
      if (((parseInt(this.editEnrollmentCap).toString().trim()) === this.editEnrollmentCap.toString().trim()) && (parseInt(this.editEnrollmentCap)>=0)) {
        // at this point it looks like an int....
        if (parseInt(this.editEnrollmentCap) !== this.initialEnrollmentData) {
          console.log('need to update enrollment!');
          updateEnrollmentCap = true;
          numChanges = numChanges + 1;
        }
      } else {
        console.log('enrollment error: ', this.editEnrollmentCap, ' ', typeof this.editEnrollmentCap);
        this.enrollmentErrorMessage = "Please make sure that the enrollment cap is an integer greater than or equal to zero."
        formOK = false;
      }
      // this.editSemesterFraction could be an int or a string, but in either case, parseInt should return the appropriate string
      if (parseInt(this.editSemesterFraction)!==parseInt(this.initialSemesterFractionData)) {
        console.log('need to update semester fraction!');
        updateSemesterFraction = true;
        numChanges = numChanges + 1;
      }
      
      if ((+this.editDeliveryMethodId) !== (+this.initialDeliveryMethodId)) {
        updateDeliveryMethod = true;
        numChanges = numChanges + 1;
      }

      this.editMeetings.forEach(meeting => {
        if (meeting.id !== null && meeting.delete === true) {
          meetingsToDelete.push(meeting.id);
        } else if (meeting.delete === false) {
          // check if need to make updates....
          if (meeting.begin_at !== "" || meeting.end_at !== "") {
            if (meeting.id === null) {
              let checkTime = this.checkTimes(meeting.begin_at, meeting.end_at);
              let roomIds = [];
              meeting.rooms.forEach( room => {
                if ((+room.id) !== NO_ROOM_SELECTED_ID) {
                  roomIds.push(+room.id);
                }
              });
              if (checkTime.timesOK) {
                meetingsToCreate.push({
                  day: parseInt(meeting.day),
                  begin_at: meeting.begin_at,
                  end_at: meeting.end_at,
                  //roomId: (+meeting.room.id) === NO_ROOM_SELECTED_ID ? null : +meeting.room.id,
                  roomIds: roomIds
                });
              } else {
                this.meetingFormErrorMessage = checkTime.errorMessage;
                formOK = false;
              }
            } else {
              let checkTime = this.checkTimes(meeting.begin_at, meeting.end_at);
              // now check if anything is different....
              //let timesIdentical = true;
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

                let roomIdsInForm = [];
                meeting.rooms.forEach( room => {
                  if ((+room.id) !== NO_ROOM_SELECTED_ID) {
                    roomIdsInForm.push(+room.id);
                  }
                });

                if (foundMeeting) {
                  // meeting.day could come from the form, so it might be a string....
                  
                  let initialRoomIds = [];
                  matchingMeeting.rooms.forEach( room => {
                    if ((+room.id) !== NO_ROOM_SELECTED_ID) {
                      initialRoomIds.push(+room.id);
                    }
                  });
                
                  timesAndRoomsIdentical = this.listsIdentical(initialRoomIds, roomIdsInForm) &&
                    matchingMeeting.day === parseInt(meeting.day) &&
                    matchingMeeting.begin_at === meeting.begin_at &&
                    matchingMeeting.end_at === meeting.end_at;
                    // && 
                    //matchingMeeting.room.id === +meeting.room.id;
                  console.log('times and rooms identical? ', timesAndRoomsIdentical);
                } else {
                  console.log(
                    "something is wrong! cannot find the id for the update...."
                  );
                }
                
                if (!timesAndRoomsIdentical) {
                  meetingsToUpdate.push({
                    id: meeting.id,
                    day: parseInt(meeting.day),
                    begin_at: meeting.begin_at,
                    end_at: meeting.end_at,
                    //roomId: (+meeting.room.id) === NO_ROOM_SELECTED_ID ? null : +meeting.room.id,
                    roomIds: roomIdsInForm
                  });
                } else {
                  meetingsToLeave.push({
                    id: meeting.id,
                    day: parseInt(meeting.day),
                    begin_at: meeting.begin_at,
                    end_at: meeting.end_at,
                    //roomId: (+meeting.room.id) === NO_ROOM_SELECTED_ID ? null : +meeting.room.id,
                    roomIds: roomIdsInForm
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
      numChanges = numChanges +
        meetingsToCreate.length +
        meetingsToUpdate.length +
        meetingsToDelete.length;
      console.log('number of changes: ', numChanges);
      console.log('form OK: ', formOK);
      if (formOK && numChanges > 0) {
        // now post the data...
        var _this = this;
        let data_for_post = {
          courseOfferingId: this.editCourseOfferingData.courseOfferingId,
          snapshot: this.editCourseOfferingData.ichairObject.snapshot,
          hasBanner: this.editCourseOfferingData.bannerId !== null,// safer to interpret the null here than in the python code, where it will probably be converted to None(?)
          bannerId: this.editCourseOfferingData.bannerId, // in python code -- first check if hasBanner; if so, can safely get id
          hasDelta: this.editCourseOfferingData.delta !== null,// same idea as above....
          delta: this.editCourseOfferingData.delta,
          includeRoomComparisons: this.editCourseOfferingData.includeRoomComparisons,
          delete: meetingsToDelete,
          update: meetingsToUpdate,
          create: meetingsToCreate,
          updateSemesterFraction: updateSemesterFraction,
          updateEnrollmentCap: updateEnrollmentCap,
          updateDeliveryMethod: updateDeliveryMethod,
          semesterFraction: parseInt(this.editSemesterFraction),
          enrollmentCap: parseInt(this.editEnrollmentCap),
          deliveryMethodId: (+this.editDeliveryMethodId) === Number.NEGATIVE_INFINITY ? null : +this.editDeliveryMethodId
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
            console.log(jsonResponse);
            _this.courseOfferings.forEach(courseOfferingItem => {
              if (_this.editCourseOfferingData.courseOfferingIndex === courseOfferingItem.index) {
                if (jsonResponse.has_delta) {
                  courseOfferingItem.delta = jsonResponse.delta;
                } else {
                  courseOfferingItem.delta = null;
                }
                
                courseOfferingItem.ichair.snapshot = jsonResponse.snapshot;
                if (updateEnrollmentCap) {
                  courseOfferingItem.ichair.change_can_be_undone.max_enrollment = true;
                }
                if (updateSemesterFraction) {
                  courseOfferingItem.ichair.change_can_be_undone.semester_fraction = true;
                }
                if (updateDeliveryMethod) {
                  courseOfferingItem.ichair.change_can_be_undone.delivery_method = true;
                }
                if ((meetingsToDelete.length > 0) || (meetingsToUpdate.length > 0) || (meetingsToCreate.length > 0)) {
                  console.log('meetings have been updated....');
                  courseOfferingItem.ichair.change_can_be_undone.meeting_times = true;
                }
                  
                courseOfferingItem.ichair.meeting_times_detail = jsonResponse.meeting_times_detail;
                /*
                courseOfferingItem.ichair.meeting_times_detail.forEach( mtd => {
                  if (mtd.room === null) {
                    mtd.room = {
                      id: NO_ROOM_SELECTED_ID,
                      short_name: "-----",
                      capacity: -1
                    };
                  }
                });
                */

                courseOfferingItem.ichair.meeting_times = jsonResponse.meeting_times;
                courseOfferingItem.ichair.rooms = jsonResponse.rooms;
                courseOfferingItem.ichair.max_enrollment = jsonResponse.max_enrollment;
                courseOfferingItem.ichair.semester_fraction = jsonResponse.semester_fraction;
                courseOfferingItem.ichair.delivery_method = {
                  id: jsonResponse.delivery_method.id,
                  code: jsonResponse.delivery_method.code,
                  description: jsonResponse.delivery_method.description
                }

                if (jsonResponse.has_delta) {
                  courseOfferingItem.schedulesMatch = jsonResponse.schedules_match || jsonResponse.delta.request_update_meeting_times;
                  courseOfferingItem.enrollmentCapsMatch = jsonResponse.max_enrollments_match || jsonResponse.delta.request_update_max_enrollment;
                  courseOfferingItem.semesterFractionsMatch = jsonResponse.semester_fractions_match || jsonResponse.delta.request_update_semester_fraction;
                  courseOfferingItem.deliveryMethodsMatch = jsonResponse.delivery_methods_match || jsonResponse.delta.request_update_delivery_method;
                } else {
                  courseOfferingItem.schedulesMatch = jsonResponse.schedules_match;
                  courseOfferingItem.enrollmentCapsMatch = jsonResponse.max_enrollments_match;
                  courseOfferingItem.semesterFractionsMatch = jsonResponse.semester_fractions_match;
                  courseOfferingItem.deliveryMethodsMatch = jsonResponse.delivery_methods_match;
                }
                courseOfferingItem.allOK =
                  courseOfferingItem.enrollmentCapsMatch &&
                  courseOfferingItem.instructorsMatch &&
                  courseOfferingItem.schedulesMatch &&
                  courseOfferingItem.semesterFractionsMatch &&
                  courseOfferingItem.publicCommentsMatch &&
                  courseOfferingItem.deliveryMethodsMatch;
                courseOfferingItem.classroomsUnassignedWarning = "";
              }
            });
            _this.cancelMeetingsForm();
          },
          error: function(jqXHR, exception) {
            // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
            console.log(jqXHR);
            _this.meetingFormErrorMessage =
              "Sorry, there appears to have been an error.";
          }
        });
      } else if (formOK && numChanges === 0) {
        this.cancelMeetingsForm();
      }
    },
    listsIdentical(list1, list2) {
      // lists are assumed to contain integers
      let listsMatch = true;
      let localList1 = JSON.parse(JSON.stringify(list1));
      let localList2 = JSON.parse(JSON.stringify(list2));

      if (localList1.length !== localList2.length) {
        listsMatch = false;
      } else {
        localList1.forEach( item => {
          let index = localList2.indexOf(item);
          if (index === -1) {
            listsMatch = false;
          } else {
            localList2.splice(index, 1)
          }
        });
      }
      return listsMatch;
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
      let courseData = [];
      this.courseOfferings.forEach(item => {
        if (item.delta !== null) {
          if (item.delta.messages_exist) {
            courseData.push({
              term_code: item.termCode,
              term_name: item.semester,
              crn: item.crn,
              banner: item.banner,
              ichair: item.ichair,
              delta: item.delta,
              courseOwnedByUser: item.courseOwnedByUser,
              includeRoomComparisons: item.includeRoomComparisons
            })
          }
        }
      });

      dataForPost = {
        courseData: courseData
      }

      console.log(dataForPost);

      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/generate-pdf/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(response) {
          console.log("response: ", response);
          console.log("response url", response.UUID);
          //let fname="ScheduleEdits_Biology_02-01-2020_205536.pdf";
          // https://stackoverflow.com/questions/51920230/open-pdf-in-new-window-with-ajax-call
          // I'm not doing this right....
          //var a = document.createElement('a');
          // the response needs to be a unique url of some sort...(?)  
          //a.href= "data:application/octet-stream;base64,"+response;
          //a.href = 'ScheduleEdits_Biology_02-01-2020_205536.pdf';
          //a.target = '_blank';
          //a.download = 'ScheduleEdits_Biology_02-01-2020_205536.pdf';
          //a.click();
          //console.log('response.url: ', JSON.parse(response.file_name));
          var url = '/planner/scheduleeditspdf/'+response.UUID+'/';
          window.open(url, "_blank");
          //window.location = url;
        },
        error: function(jqXHR, exception) {
          // https://stackoverflow.com/questions/6792878/jquery-ajax-error-function
          console.log(jqXHR);
          //_this.meetingFormErrorMessage =
          //  "Sorry, there appears to have been an error.";
        }
      });
    },

    filteredRoomChoices(roomId, rooms) {
      //console.log(roomId);
      //console.log(rooms);
      let otherUsedRoomIds = [];
      rooms.forEach( room => {
        if ((room.id !== roomId) && (room.id !== NO_ROOM_SELECTED_ID)) {
          otherUsedRoomIds.push(room.id);
        }
      });
      //console.log(otherUsedRoomIds);
      //https://stackoverflow.com/questions/33577868/filter-array-not-in-another-array#:~:text=You%20can%20simply%20run%20through,when%20the%20callback%20returns%20true%20.
      return this.roomChoices.filter( roomOption => !otherUsedRoomIds.includes(roomOption.id));
    },

    addRoomToMeetingTime(rooms) {
      rooms.push({
        id: NO_ROOM_SELECTED_ID,
        capacity: -1,
        short_name: ""
      })
    },

    // https://stackoverflow.com/questions/5767325/how-can-i-remove-a-specific-item-from-an-array
    dropThisRoom(index, rooms) {
      rooms.splice(index, 1);
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
      url: "/planner/ajax/fetch-semesters-and-extra-departmental-courses/", // set the url of the request
      dataType: "json",
      data: {
        departmentId: json_data.departmentId, // add the department id to the GET parameters
        yearId: json_data.yearId
      },
      success: function(incomingData) {
        console.log(incomingData);
        _this.semesterChoices = incomingData.semester_choices;
        //_this.roomRequestsAllowed = incomingData.allow_room_requests;
        _this.extraDepartmentalCourseChoices = incomingData.extra_courses_this_year;
        _this.chosenExtraCourses = [];
        _this.extraDepartmentalSubjectChoices = [{
          id: Number.NEGATIVE_INFINITY,
          abbrev: '-----'
        }];
        _this.extraDepartmentalCourseChoices.forEach(course => {
          _this.chosenExtraCourses.push(course.id);
        });
        _this.extraDepartmentalSubjectAndCourseChoices = incomingData.extra_departmental_course_choices;
        _this.extraDepartmentalSubjectAndCourseChoices.forEach(subject => {
          _this.extraDepartmentalSubjectChoices.push({
            id: subject.id,
            abbrev: subject.abbrev
          });
        });
        _this.registrarCourseOfferingsExist = incomingData.banner_data_exists;
      }
    });
  }
});

