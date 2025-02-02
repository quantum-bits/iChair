// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const
const CREATE_NEW_COURSE = -2;
const DO_NOTHING = -1;

const CREATE_NEW_COURSE_OFFERING = -2;
const DELETE_BANNER_COURSE_OFFERING = -3;
const DELETE_ICHAIR_COURSE_OFFERING = -4;

const DELTA_ACTION_CREATE = "create"; // used for delta course offerings; note that these are actions that the registrar is being asked to
const DELTA_ACTION_UPDATE = "update"; // perform, not the actions that are being performed here on the delta objects
const DELTA_ACTION_DELETE = "delete";
const DELTA_ACTION_NO_ACTION = "no_action";
const DELTA_ACTION_SET = "deltaUpdateSet"; // turn off the update
const DELTA_ACTION_UNSET = "deltaUpdateUnset"; // turn off the update

const DELTA_UPDATE_TYPE_MEETING_TIMES = "meetingTimes";
const DELTA_UPDATE_TYPE_INSTRUCTORS = "instructors";
const DELTA_UPDATE_TYPE_SEMESTER_FRACTION = "semesterFraction";
const DELTA_UPDATE_TYPE_ENROLLMENT_CAP = "enrollmentCap";
const DELTA_UPDATE_TYPE_COMMENTS = "publicComments";
const DELTA_UPDATE_TYPE_DELIVERY_METHOD = "deliveryMethod";
const DELTA_UPDATE_TYPE_MARK_OK = "manuallyMarkedOK";

const COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT = "enrollmentCap";
const COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION = "semesterFraction";
const COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS = "instructors";
const COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES = "meetingTimes";
const COPY_REGISTRAR_TO_ICHAIR_COMMENTS = "publicComments";
const COPY_REGISTRAR_TO_ICHAIR_DELIVERY_METHOD = "deliveryMethod";
const COPY_REGISTRAR_TO_ICHAIR_ALL = "all";

const NO_ROOM_SELECTED_ID = Number.NEGATIVE_INFINITY;
const NO_DELIVERY_METHOD_SELECTED_ID = Number.NEGATIVE_INFINITY;

const HELP_MESSAGE_MANUAL_MARK_OK = 0;
const HELP_MESSAGE_NOTE_FOR_REGISTRAR = 1;
const HELP_MESSAGE_NOTE_TO_SELF = 2;

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
      DELTA_UPDATE_TYPE_MARK_OK: DELTA_UPDATE_TYPE_MARK_OK,
      DELTA_ACTION_SET: DELTA_ACTION_SET,
      DELTA_ACTION_UNSET: DELTA_ACTION_UNSET,
      DELTA_ACTION_CREATE: DELTA_ACTION_CREATE,
      DELTA_ACTION_UPDATE: DELTA_ACTION_UPDATE,
      DELTA_ACTION_DELETE: DELTA_ACTION_DELETE,
      DELTA_ACTION_NO_ACTION: DELTA_ACTION_NO_ACTION,
      COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT: COPY_REGISTRAR_TO_ICHAIR_ENROLLMENT,
      COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION: COPY_REGISTRAR_TO_ICHAIR_SEMESTER_FRACTION,
      COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS: COPY_REGISTRAR_TO_ICHAIR_INSTRUCTORS,
      COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES: COPY_REGISTRAR_TO_ICHAIR_MEETING_TIMES,
      COPY_REGISTRAR_TO_ICHAIR_COMMENTS: COPY_REGISTRAR_TO_ICHAIR_COMMENTS,
      COPY_REGISTRAR_TO_ICHAIR_DELIVERY_METHOD: COPY_REGISTRAR_TO_ICHAIR_DELIVERY_METHOD,
      COPY_REGISTRAR_TO_ICHAIR_ALL: COPY_REGISTRAR_TO_ICHAIR_ALL,
      HELP_MESSAGE_MANUAL_MARK_OK: HELP_MESSAGE_MANUAL_MARK_OK,
      HELP_MESSAGE_NOTE_FOR_REGISTRAR: HELP_MESSAGE_NOTE_FOR_REGISTRAR,
      HELP_MESSAGE_NOTE_TO_SELF: HELP_MESSAGE_NOTE_TO_SELF,
      helpDialog: false, // set to true to display the help dialog
      helpDialogTitle: '',
      helpDialogMessages: [],
      semesterFractionsReverse: {}, // used to convert
      semesterFractions: {},
      semesterFractionsDropdown: [], // used for a drop-down menu
      choosingSemesters: true, // set to false once semesters have been chosen to work on
      semesterChoices: [], // filled in via an ajax request after the component is mounted
      roomRequestsAllowed: false, // true if room requests are allowed for one of the chosen semesters
      showStaleMessagesDialog: false,
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
      search: '',
      json_data: json_data,
      page: 1,
      pageCount: 0,
      itemsPerPage: 15,
      showAllCourses: false,
      buttonRipple: false,
      staleMessagesHeaders: [
        { text: "Course", value: "course", width:"110px" },
        { text: "CRN", value: "crn", width:"80px" },
        { text: "Semester", value: "semester", width:"60px" },
        { text: "Last Update", value: "deltaUpdatedAt", width:"160px"},
        { text: "Message", value: "text", width:"250px" },
        { text: "Actions", value: "", width:"150px"}
      ],
      headers: [
        { text: "Semester", value: "semester" },
        { text: "Code", value: "termCode" },
        { text: "CRN", value: "crn" },
        { text: "Linked/Note", value: "linked"},
        { text: "CMP", value: "campus"},
        {
          text: "Number",
          align: "left",
          sortable: true,
          value: "course"
        },
        { text: "Name", value: "name", align: "left" },
        { text: "Credit Hours", value: "creditHours", align: "left" },
        { text: "Status", value: "", sortable: false, align: "center" }
      ],
      showLinearProgressBar: false,
      courseOfferingAlignmentPhaseReady: false, // set to true once we're ready to start comparing course offerings
      courseOfferings: [],
      numberPrimaryInstructorsIncorrectDialog: false, // set to true in order to display a message about the number of primary instructors being incorrect
      newCourseOfferingDialog: false, // true when the new course offering dialog is being displayed
      deleteIChairCourseOfferingDialog: false, // true when the delete iChair course offering dialog is being displayed
      publicCommentsDialog: false, // true when the public comments dialog is being displayed
      commentForRegistrarOrSelfDialog: false, // true when the comment for registrar/self dialog is being displayed
      commentForRegistrarOrSelf: "", // used to stored a comment for the registrar/self
      isRegistrarNote: true, // true if the current comment (in the dialog) is for the registrar; false if it is a note to self
      maxLengthRegistrarOrSelfNote: 500, // max number of characters for the note to the registrar or to self
      courseChoices: [], // used in the new course offering dialog when choosing which course to associate with a course offering that is about to be created
      courseChoice: null, // the course chosen in the new course offering dialog
      newCourseOfferingDialogItem: null, // the courseOfferings 'item' relevant for the new course offering dialog
      newCourseOfferingDialogCourseText: "", // some text displayed in the new course offering dialog
      newCourseOfferingDialogErrorMessage: "", // error message used in the new course offering dialog
      deleteIChairCourseOfferingDialogItem: null, // the courseOfferings 'item' relevant for the delete iChair course offering dialog
      deleteIChairCourseOfferingDialogCourseText: "", // some text displayed in the delete iChair course offering dialog
      //deleteIChairCourseOfferingDialogErrorMessage: "", // error message used in the delete iChair course offering dialog
      deleteIChairCourseOfferingDialogSemester: "", // semester for the iChair course to be deleted (used for display in delete iChair course offering dialog)
      deleteIChairCourseOfferingDialogMeetings: [], // meeting information for the iChair course to be deleted (used for display in delete iChair course offering dialog)
      deleteIChairCourseOfferingDialogInstructors: [], // instructor information for the iChair course to be deleted (used for display in delete iChair course offering dialog)
      dialog: false, // true when the dialog is being displayed
      dialogTitle: "",
      editInstructorsDialog: false, // true when the dialog is being displayed
      editMeetings: [], // used to store the data in the class schedule form
      editInstructors: [], // used to store the data in the edit instructors form
      editEnrollmentCap: null, // used to store enrollment data in the class schedule form
      editLoadAvailable: null, // used to store "load available" data in the edit intructors form
      editSemesterFraction: null, // used to store semester fraction data in the class schedule form
      editSemesterId: null, // used to store semester data in the class schedule form
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
    isSuper() {
      return json_data.isSuper;
    },
    launchHelpDialog(helpDialogType) {
      if (helpDialogType === HELP_MESSAGE_MANUAL_MARK_OK) {
        this.helpDialogTitle = "Manually mark as OK";
        this.helpDialogMessages = [
          {
            isText: true,
            text: "If there is not perfect agreement between iChair and the Registrar's database for this course offering, you may wish to manually mark this course offering as OK.  This will turn the ",
            isWarning: false,
            isPrimary: false,
            icon: ""
          },
          {
            isText: false,
            text: "",
            isWarning: true,
            isPrimary: false,
            icon: "mdi-alert"
          },
          {
            isText: true,
            text: " icon into ",
            isWarning: false,
            isPrimary: false,
            icon: ""
          },
          {
            isText: false,
            text: "",
            isWarning: false,
            isPrimary: false,
            icon: "mdi-alert"
          },
          {
            isText: true,
            text: " .  (That's all it does.)  You may also wish to Add a Note to Self explaining why you are doing this.",
            isWarning: false,
            isPrimary: false,
            icon: ""
          },

        ];
      } else if (helpDialogType === HELP_MESSAGE_NOTE_TO_SELF) {
        this.helpDialogTitle = "Note to Self";
        this.helpDialogMessages = [
          {
            isText: true,
            text: "You can create a Note to Self to remind yourself why you did something or what you need to do at some point in the future.  Notes to Self will not be included in your Schedule Edits pdf.",
            isWarning: false,
            isPrimary: false,
            icon: ""
          },
        ];
      } else if (helpDialogType === HELP_MESSAGE_NOTE_FOR_REGISTRAR) {
        this.helpDialogTitle = "Note for Registrar";
        this.helpDialogMessages = [
          {
            isText: true,
            text: "You can create a Note for the Registrar to let the registrar's office know something about this course section.  Please do not include requests such as 'Delete this section' or 'Change the time to MWF 9:00-9:50'. Instead, change those properties in the iChair version of the course (in the left column) and then use the ",
            isWarning: false,
            isPrimary: false,
            icon: ""
          },
          {
            isText: false,
            text: "",
            isWarning: false,
            isPrimary: true,
            icon: "mdi-arrow-right-bold-circle"
          },
          {
            isText: true,
            text: " icon to request that the registrar make the corresponding change.",
            isWarning: false,
            isPrimary: false,
            icon: ""
          }
        ];
      }
      this.helpDialog = true;
    },

    closeHelpDialog() {
      this.helpDialogTitle = "";
      this.helpDialogMessages = [];
      this.helpDialog = false;
    },

    launchStaleMessagesDialog() {
      this.showStaleMessagesDialog = true;
    },

    deleteNoteForRegistrar(item) {
      // deletes a note for the registrar
      console.log(item);
      this.courseOfferings.forEach(courseOfferingItem => {
        if (item.index === courseOfferingItem.index) {
          let courseInfo = JSON.parse(JSON.stringify(courseOfferingItem));
          this.deleteNoteForRegistrarOrSelf(courseInfo, true);
        }
      });
    },

    refreshNoteForRegistrar(item) {
      // resets the time stamp for a note for the registrar so that it disappears from the "stale messages" list for a few days
      console.log(item);
      // WORKING HERE
      let courseInfo = null;
      this.courseOfferings.forEach(courseOfferingItem => {
        if (item.index === courseOfferingItem.index) {
          courseInfo = JSON.parse(JSON.stringify(courseOfferingItem));
        }
      });
      if (courseInfo !== null) {
        console.log('refresh the note!', courseInfo);
        this.editCourseOfferingData = {
          courseOfferingIndex: courseInfo.index,//useful for fetching the course offering item back later on, in order to make changes
        };
        let noteInfo = {
          isRegistrarNote: true,
          deltaId: courseInfo.delta.id,
          hasDelta: true,
          action: DELTA_ACTION_UPDATE,
          text: item.text,
          iChairId: courseInfo.hasIChair ? courseInfo.ichair.course_offering_id : null,
          bannerId: courseInfo.hasBanner ? courseInfo.banner.course_offering_id : null,
          hasIChair: courseInfo.hasIChair, // but doesn't matter
          hasBanner: courseInfo.hasBanner, // but doesn't matter
          includeRoomComparisons: courseInfo.includeRoomComparisons,
          semesterId: courseInfo.semesterId
        }
        this.createUpdateDeleteNoteForRegistrarOrSelf(noteInfo);
      } else {
        console.log('ERROR!  Could not refresh the note....');
      }
    },

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
                inactive_after: null,
                capacity: -1
              };
            let noDeliveryMethod = {
              id: NO_DELIVERY_METHOD_SELECTED_ID,
              code: "",
              description: "-----",
            };
            _this.roomChoices = incomingData.available_rooms;
            _this.roomChoices.unshift(noRoom);
            console.log("rooms: ", _this.roomChoices);
            //console.log("semesters: ", _this.semesterChoices);
            _this.deliveryMethodChoices = incomingData.available_delivery_methods;
            _this.deliveryMethodChoices.unshift(noDeliveryMethod);
            incomingData.course_data.forEach(course => {
              let ichairChoices = [];
              let showIChairRadioSelect = false;

              if (!course.has_ichair) {
                ichairChoices = _this.constructIChairChoices(course.ichair_options);
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
                bannerChoices = _this.constructBannerChoices(course.banner_options);

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
                courseOwnedByUser: course.course_owned_by_user,
                termCode: course.term_code,
                allowRoomRequests: course.allow_room_requests,// whether room edit requests may be made for this semester (regardless of whether the user wants to do them)
                includeRoomComparisons: course.include_room_comparisons,// whether to include room comparisons as part of the meeting time comparisons
                course: course.course,
                creditHours: course.credit_hours,
                name: course.course_title,
                crn: course.crn,
                campus: course.campus,
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
                numberPrimaryInstructorsIncorrectMessage: "", // used to display a message saying that the number of primary instructors is incorrect
                manuallyMarkedOK: course.delta === null ? false : course.delta.manually_marked_OK
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
    constructIChairChoices(ichairOptions) {
      let ichairChoices = [];
      ichairOptions.forEach(ichairOption => {
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
      return ichairChoices;
    },

    constructBannerChoices(bannerOptions) {
      let bannerChoices = [];
      bannerOptions.forEach(bannerOption => {
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
      bannerChoices.push({
        selectionId: DELETE_ICHAIR_COURSE_OFFERING, //assuming that course offering ids are always non-negative
        text:
          "Delete this course offering in iChair"
      });
      return bannerChoices;
    },

    deactivateScheduleRightArrow(item) {
      if (this.isSuper()) {
        return true;
      }
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
      if (this.isSuper()) {
        return true;
      }
      return item.schedulesMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateInstructorsRightArrow(item) {
      if (this.isSuper()) {
        return true;
      }
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
      if (this.isSuper()) {
        return true;
      }
      return item.instructorsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateMaxEnrollmentRightArrow(item) {
      if (this.isSuper()) {
        return true;
      }
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
      if (this.isSuper()) {
        return true;
      }
      return item.enrollmentCapsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateDeliveryMethodRightArrow(item) {
      if (this.isSuper()) {
        return true;
      }
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
      if (this.isSuper()) {
        return true;
      }
      return item.deliveryMethodsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivateSemesterFractionRightArrow(item) {
      if (this.isSuper()) {
        return true;
      }
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
      if (this.isSuper()) {
        return true;
      }
      return item.semesterFractionsMatch || !item.hasIChair || !item.hasBanner;
    },
    deactivatePublicCommentsRightArrow(item) {
      if (this.isSuper()) {
        return true;
      }
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
      if (this.isSuper()) {
        return true;
      }
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
      //} else if (item.ichairChoice === DELETE_ICHAIR_COURSE_OFFERING) {
      //  console.log("delete ichair course offering!");
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
          campus: item.campus,
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
          campus: item.campus,
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
            item.manuallyMarkedOK = item.delta === null ? false : item.delta.manually_marked_OK;
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

    launchDeleteIChairCourseOfferingDialog(item) {
      console.log(item);
      let creditText = item.ichair.credit_hours === 1 ? " credit hour)" : " credit hours)";
      this.deleteIChairCourseOfferingDialogCourseText =
              item.ichair.course +
              " - " +
              item.ichair.course_title +
              " (" + 
              item.ichair.credit_hours +
              creditText;
      this.deleteIChairCourseOfferingDialogItem = JSON.parse(JSON.stringify(item));
      this.deleteIChairCourseOfferingDialogSemester =  item.semester;
      this.deleteIChairCourseOfferingDialogMeetings = [];
      // https://stackoverflow.com/questions/10179815/get-loop-counter-index-using-for-of-syntax-in-javascript
      for (let i = 0; i < item.ichair.meeting_times.length; i++) {
        this.deleteIChairCourseOfferingDialogMeetings.push(
          item.ichair.meeting_times[i] + " / " + item.ichair.rooms[i]
        );
      }
      this.deleteIChairCourseOfferingDialogInstructors = [];
      item.ichair.instructors_detail.forEach(instructor => {
        this.deleteIChairCourseOfferingDialogInstructors.push(instructor.name);
      });
      this.deleteIChairCourseOfferingDialog = true;
    },

    cancelDeleteIChairCourseOfferingDialog() {
      //this.newCourseOfferingDialogErrorMessage = "";
      this.deleteIChairCourseOfferingDialog = false;
      this.deleteIChairCourseOfferingDialogSemester = "";
      this.deleteIChairCourseOfferingDialogMeetings = [];
      this.deleteIChairCourseOfferingDialogInstructors = [];
      //reset the choice change that launched the dialog in the first place
      this.courseOfferings.forEach(item => {
        if (item.index === this.deleteIChairCourseOfferingDialogItem.index) {
          item.bannerChoice = null;
        }
      })
      this.deleteIChairCourseOfferingDialogItem = null; // we had made a copy of the item (using the JSON.parse() trick), so we're OK to set it to null
    },

    unlinkedIChairCourseOfferingIds() {
      // returns a list of course offering ids for all currently unlinked iChair course offerings
      unlinkedIds = [];
      this.courseOfferings.forEach( courseOffering => {
        if (courseOffering.hasIChair && !courseOffering.hasBanner) {
          unlinkedIds.push(courseOffering.ichair.course_offering_id);
        }
      });
      return unlinkedIds;
    },

    deleteIChairCourseOffering() {
      console.log('delete the following:', this.deleteIChairCourseOfferingDialogItem.ichair.course_offering_id);
      var _this = this;
      $.ajax({
        type: "POST",
        url: "/planner/ajax/delete-course-offering/",
        dataType: "json",
        data: JSON.stringify({
          courseOfferingId: this.deleteIChairCourseOfferingDialogItem.ichair.course_offering_id,
          deltaId: this.deleteIChairCourseOfferingDialogItem.delta === null ? null : this.deleteIChairCourseOfferingDialogItem.delta.id,
          hasBanner: this.deleteIChairCourseOfferingDialogItem.hasBanner,
          unlinkedIChairCourseOfferingIds: this.unlinkedIChairCourseOfferingIds(),
          bannerCourseOfferingId: this.deleteIChairCourseOfferingDialogItem.hasBanner === false ? null : this.deleteIChairCourseOfferingDialogItem.banner.course_offering_id,
          departmentId: json_data.departmentId,
          yearId: json_data.yearId,
          termCode: this.deleteIChairCourseOfferingDialogItem.termCode
        }),
        success: function(jsonResponse) {
          console.log("response: ", jsonResponse);
          if (!_this.deleteIChairCourseOfferingDialogItem.hasBanner) {
            // in this case, the iChair course was not linked to a Banner course offering, 
            // so it was in the courseOfferings list and now needs to be popped out....
            _this.removeUnlinkedIChairItemFromCourseOfferings(
              null,
              jsonResponse.course_offering_id
            );
          } else {
            // the iChair course offering was linked with a Banner course offering, so now need to do some clean-up....
            // first, clean up the courseOffering item that now only contains the banner course offering....
            _this.courseOfferings.forEach(courseOfferingItem => {
              if (_this.deleteIChairCourseOfferingDialogItem.index === courseOfferingItem.index) {
                // found the one we're working on
                courseOfferingItem.allOK = false;
                courseOfferingItem.deliveryMethodsMatch = false;
                courseOfferingItem.delta = jsonResponse.delta_course_offering;
                courseOfferingItem.enrollmentCapsMatch = false;
                courseOfferingItem.hasIChair = false;
                courseOfferingItem.ichair = null;
                courseOfferingItem.ichairChoice = null;
                courseOfferingItem.ichairChoices = _this.constructIChairChoices(jsonResponse.ichair_options);
                courseOfferingItem.ichairOptions = jsonResponse.ichair_options;
                courseOfferingItem.instructorsMatch = false;
                courseOfferingItem.linked = false;
                courseOfferingItem.publicCommentsMatch = false;
                courseOfferingItem.schedulesMatch = false;
                courseOfferingItem.semesterFractionsMatch = false;
                courseOfferingItem.showAllIChairComments = false;
                courseOfferingItem.showCourseOfferingRadioSelect = true;
                courseOfferingItem.manuallyMarkedOK = false;
                // clear out any error/warning messages that might have been displayed for the iChair course offering; 
                // these are no longer relevant
                courseOfferingItem.errorMessage = '';
                courseOfferingItem.loadsAdjustedWarning = '';
                courseOfferingItem.classroomsUnassignedWarning = '';
                courseOfferingItem.numberPrimaryInstructorsIncorrectMessage = '';
              }
            });
            // now cycle through certain unlinked iChair course offerings to update their bannerOptions and bannerChoices, since now,
            // for these particular unlinked ico's, there is a new unlinked bco (i.e., the one that we just deleted the ico for....)
            jsonResponse.banner_options_for_unlinked_ichair_course_offerings.forEach( ico => {
              console.log('unlinked ico: ', ico);
              _this.courseOfferings.forEach(courseOfferingItem => {
                if (courseOfferingItem.hasIChair) {
                  console.log('course offering item id: ', courseOfferingItem.ichair.course_offering_id);
                  if (courseOfferingItem.ichair.course_offering_id === ico.ico_id) {
                    console.log('we have a winner!');
                    courseOfferingItem.bannerOptions = ico.banner_options;
                    courseOfferingItem.bannerChoices = _this.constructBannerChoices(ico.banner_options);
                  };
                }
              });
            });
            console.log(_this.courseOfferings);
          };
          _this.cancelDeleteIChairCourseOfferingDialog();
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
        campus: item.campus,
        loadAvailable: item.creditHours, //need to warn the user that this has been set automatically; we actually compute the load available in api_views.py now (different for summer courses, OCD, OCP and ECC)
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
              courseOfferingItem.manuallyMarkedOK = courseOfferingItem.delta === null ? false : courseOfferingItem.delta.manually_marked_OK;
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
          // now need to pop the banner option out of the list for any unlinked iChair course offerings
          _this.removeChoicesAndOptions(jsonResponse.banner_course_offering_id, null);
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
      // removes these course offerings from the list of options for other course offerings;
      // can also be used after deleting an unlinked iChair course offering; in this case, 
      // bannerCourseOfferingId is passed in as null;
      // can also be used after creating a new iChair course offering and immediately linking
      // it with its corresponding Banner course offering; in this case, iChairCourseOfferingId
      // is passed in as null (only want to remove the Banner course offering as a choice or 
      // option for other iChair course offerings)
      if (bannerCourseOfferingId !== null) {
        this.courseOfferings.forEach(item => {
          item.bannerChoices = item.bannerChoices.filter(
            choice => !this.removeChoice(choice, bannerCourseOfferingId)
          );
        });
        this.courseOfferings.forEach(item => {
          item.bannerOptions = item.bannerOptions.filter(
            option => !this.removeOption(option, bannerCourseOfferingId)
          );
        });
      };
      if (iChairCourseOfferingId !== null) {
        this.courseOfferings.forEach(item => {
          item.ichairChoices = item.ichairChoices.filter(
            choice => !this.removeChoice(choice, iChairCourseOfferingId)
          );
        });
        this.courseOfferings.forEach(item => {
          item.ichairOptions = item.ichairOptions.filter(
            option => !this.removeOption(option, iChairCourseOfferingId)
          );
        });
      }
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
      // bannerChoices (listing used for a radio select), and likewise for the (now linked) iChair course offering;
      // can also be used after deleting an unlinked iChair course offering; in this case, 
      // bannerCourseOfferingId is passed in as null
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
      console.log("course offerings length: ", this.courseOfferings.length);
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
        dataForPost = {
          deltaMods: {
            instructors: true,
            meetingTimes: true,
            enrollmentCap: true,
            semesterFraction: true,
            publicComments: true,
            deliveryMethod: true,
          }, // request all delta mods by default when issuing a "create" request to the registrar
          deltaId: null, // there could be a no_action delta, but set to null, since we have only just linked the Banner course offering with the iChair one
          //bannerNoteToSelf: null,
          //iChairNoteToSelf: item.delta === null ? null : item.delta.note_to_self, // could be there if these is a no_action delta; in this case, pass in a possible note_to_self
          action: DELTA_ACTION_CREATE,
          crn: null, // doesn't exist yet
          campus: null, // doesn't exist yet
          iChairCourseOfferingId: item.ichair.course_offering_id,
          bannerCourseOfferingId: null, // don't have one, since we're requesting that the registrar create one
          semesterId: item.semesterId,
          includeRoomComparisons: item.includeRoomComparisons
        };
        item.showBannerCourseOfferingRadioSelect = false;
      } else if (item.bannerChoice === DELETE_ICHAIR_COURSE_OFFERING) {
        console.log("delete ichair course offering!");
        this.launchDeleteIChairCourseOfferingDialog(item);
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
            item.campus = bannerOption.campus;
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
          deltaId: null, // there could be a no_action delta, but set to null, since we have only just linked the Banner course offering with the iChair one
          //bannerNoteToSelf: null, // we are linking a bco to an ico; is there a way to get a possible bannerNoteToSelf to pass in?
          //iChairNoteToSelf: item.delta === null ? null : item.delta.note_to_self, // could be there if these is a no_action delta; in this case, pass in a possible note_to_self
          action: DELTA_ACTION_UPDATE,
          crn: item.crn,
          campus: item.campus,
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

      if (item.bannerChoice !== DELETE_ICHAIR_COURSE_OFFERING) {
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
            item.manuallyMarkedOK = item.delta === null ? false : item.delta.manually_marked_OK;
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
            inactive_after: null,
            capacity: -1
          });
        }
        // the id property can be edited in the dialog...and will get out of sync with the short_name and capacity, so those are
        // being altered here.  There must be a better way to do this, but vue wants to set the v-model to a property of an object
        // that is being iterated over....  In any case, we will only use the id later on.
        meeting.rooms.forEach( room => {
          room.short_name = "";
          room.inactive_after = null;
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
      this.editSemesterId = courseInfo.semesterId;
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
                courseOfferingItem.manuallyMarkedOK = courseOfferingItem.delta === null ? false : courseOfferingItem.delta.manually_marked_OK;
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
      //  - if a delta object of type 'delete', 'update' or 'create' already exists, but there is not yet a comment, then true
      //  - if no delta object exists yet, or the one that does exist is of type 'no_action' (and there is not yet a comment):
      //    - if only have a course offering in iChair, then false (user needs to request that the Banner create a course offering first)
      //    - if only have a course offering in Banner, then false (user should request a "delete" or should copy the course offering over to iChair first)
      //    - if the course offering exists in iChair and in Banner, then true (and if the button is clicked, create a delta of "update" type)
      if (courseInfo.delta === null) {
        // a delta object does not exist
        return courseInfo.hasIChair && courseInfo.hasBanner;
      } else if (courseInfo.delta.requested_action === DELTA_ACTION_NO_ACTION) {
        // a delta object does exist and it is of type 'no_action' (the second part about the comment already existing
        // shouldn't really ever happen, since when a comment is made, the requested_action will change to 'update'; also,
        // the first part shouldn't happen, either, since this should be an 'update' action if we have both a bco and an ico....)
        return (courseInfo.hasIChair && courseInfo.hasBanner) && (!courseInfo.delta.registrar_comment_exists);
      } else {
        return !courseInfo.delta.registrar_comment_exists;
      }
    },

    displayAddNoteToSelfButton(courseInfo) {
      if (courseInfo.delta === null) {
        // a delta object does not exist
        return true;
      } else {
        return ((courseInfo.delta.note_to_self === null) || (courseInfo.delta.note_to_self === ''));
      }
    },

    disableManuallyMarkAsOKOption(courseInfo) {
      return courseInfo.allOK || this.isSuper();
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

    displayNoteDialog(courseInfo, isRegistrarNote) {
      // if isRegistrarNote === true, then the dialog displays a "note for the Registrar" (to be included with the schedule edits pdf);
      // otherwise, this is a "note to self"
      if (isRegistrarNote) {
        console.log('display registrar note!');
      } else {
        console.log('display note to self!');
      }
      
      let bannerId = null;
      let iChairId = null;
      if (courseInfo.hasBanner) {
        bannerId = courseInfo.banner.course_offering_id;
      }
      if (courseInfo.hasIChair) {
        iChairId = courseInfo.ichair.course_offering_id;
      }
      if (courseInfo.delta !== null) {
        if (isRegistrarNote) {
          this.maxLengthRegistrarOrSelfNote = 500;
          if (courseInfo.delta.registrar_comment_exists) {
            this.commentForRegistrarOrSelf = courseInfo.delta.registrar_comment;
          } else {
            this.commentForRegistrarOrSelf = "";
          }
        } else {
          // if the note is for a "singleton" type of delta object (delete, create or no_action, allow 250 characters);
          // if the notes is for an "update" delta object, allow the full 700 characters that are allowed by the data model;
          // the reason for this is that if "singleton" delta objects are "combined" into an "update" object, the notes to self
          // are merged, along with some explanatory text;
          // this is not ideal, since the user could have a long note for an "update" delta, and then delete the ico, so that it
          // converts to the shorter note length; the db will still allow the longer note, but if they go to edit it, they will
          // be forced to shorten it before submitting...ah well....
          // also going back and forth between delta types, and auto-merging notes to self could lead to a situation where two 
          // longer notes get merged and the length is longer than the max lenght; fortunately the server handles this OK (it just
          // truncates the string to the max length, which is OK....)
          if (courseInfo.delta.requested_action === this.DELTA_ACTION_UPDAT) {
            this.maxLengthRegistrarOrSelfNote = 700;
          } else {
            this.maxLengthRegistrarOrSelfNote = 250;
          }
          if ((courseInfo.delta.note_to_self !== null) && (courseInfo.delta.note_to_self !== '')) {
            this.commentForRegistrarOrSelf = courseInfo.delta.note_to_self;
          } else {
            this.commentForRegistrarOrSelf = "";
          }
        }
      } else {
        this.commentForRegistrarOrSelf = "";
        if (this.isRegistrarNote) {
          this.maxLengthRegistrarOrSelfNote = 500;
        } else {
          // there is no delta object, so we need to infer which type of delta object will be created....
          if (courseInfo.hasBanner && courseInfo.hasIChair) {
            // dco will be of type "update", so allow 700 characters....
            this.maxLengthRegistrarOrSelfNote = 700;
          } else {
            this.maxLengthRegistrarOrSelfNote = 250;
          }
        }
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
        includeRoomComparisons: courseInfo.includeRoomComparisons,
        semesterId: courseInfo.semesterId
      };
      this.dialogTitle = courseInfo.course + ": " + courseInfo.name;
      this.commentForRegistrarOrSelfDialog = true;
      this.isRegistrarNote = isRegistrarNote;
    },

    deleteNoteForRegistrarOrSelf(courseInfo, isRegistrarNote) {
      // used for deleting a note for the registrar or self on an existing delta object
      console.log('delete the note!', courseInfo);
      this.editCourseOfferingData = {
        courseOfferingIndex: courseInfo.index,//useful for fetching the course offering item back later on, in order to make changes
      };
      let noteInfo = {
        isRegistrarNote: isRegistrarNote,
        deltaId: courseInfo.delta.id,
        hasDelta: true,
        action: DELTA_ACTION_DELETE,
        text: null, // unimportant, since the note is going to be deleted anyways
        iChairId: courseInfo.hasIChair ? courseInfo.ichair.course_offering_id : null,
        bannerId: courseInfo.hasBanner ? courseInfo.banner.course_offering_id : null,
        hasIChair: courseInfo.hasIChair, // but doesn't matter
        hasBanner: courseInfo.hasBanner, // but doesn't matter
        includeRoomComparisons: courseInfo.includeRoomComparisons,
        semesterId: courseInfo.semesterId
      }
      this.createUpdateDeleteNoteForRegistrarOrSelf(noteInfo);
    },

    noteForRegistrarOrSelfTooLong() {
      return this.commentForRegistrarOrSelf.length > this.maxLengthRegistrarOrSelfNote;
    },

    cancelNoteForRegistrarOrSelfForm() {
      console.log('cancel note for registrar/self dialog');
      this.editCourseOfferingData = {};
      this.dialogTitle = "";
      this.commentForRegistrarOrSelfDialog = false;
      this.commentForRegistrarOrSelf = "";
      this.isRegistrarNote = true;
      this.maxLengthRegistrarOrSelfNote = 500;
    },
    submitNoteForRegistrarOrSelf() {
      // either submitting a new note or updating an existing one; if the user cleared a note by backspacing, may need to delete a note....
      console.log('submit note for registrar');
      let OKToSubmit = true;
      let hasDelta = !(this.editCourseOfferingData.delta === null);
      let deltaId = null;
      if (hasDelta) {
        deltaId = this.editCourseOfferingData.delta.id;
      }
      let text = this.commentForRegistrarOrSelf;
      if (text === "") {// user wants to delete the note....
        if (hasDelta) {
          action = 'delete'; // delete the note, not the delta object itself....
        } else {
          OKToSubmit = false;
          this.cancelNoteForRegistrarOrSelfForm();
        }
      } else { // text is not a blank string
        if (hasDelta) {
          action = 'update'; // a delta object already exists, so we're doing an update to the delta object
        } else {
          action = 'create'; // no delta object, so need to create one (which will, confusingly, be of the "update" type....)
        }
      }
      let noteInfo = {
        isRegistrarNote: this.isRegistrarNote,
        deltaId: deltaId,
        hasDelta: hasDelta,
        action: action,
        text: text,
        iChairId: this.editCourseOfferingData.iChairId,
        bannerId: this.editCourseOfferingData.bannerId,
        hasIChair: this.editCourseOfferingData.hasIChair,
        hasBanner: this.editCourseOfferingData.hasBanner,
        includeRoomComparisons: this.editCourseOfferingData.includeRoomComparisons,
        semesterId: this.editCourseOfferingData.semesterId
      }
      if (OKToSubmit) {
        this.createUpdateDeleteNoteForRegistrarOrSelf(noteInfo);
      }
    },

    createUpdateDeleteNoteForRegistrarOrSelf(noteInfo) {
      console.log('note info: ', noteInfo);
      var _this = this;
      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/create-update-delete-note-for-registrar-or-self/",
        dataType: "json",
        data: JSON.stringify(noteInfo),
        success: function(jsonResponse) {
          console.log("response: ", jsonResponse);
          _this.courseOfferings.forEach(courseOfferingItem => {
            if (_this.editCourseOfferingData.courseOfferingIndex === courseOfferingItem.index) {
              courseOfferingItem.delta = jsonResponse.delta_response;
            }
          });
          _this.cancelNoteForRegistrarOrSelfForm();
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
          // trimming white space: https://www.w3schools.com/jsref/tryit.asp?filename=tryjsref_trim
          if (comment.id === null) {
            if (comment.text.trim() !== '') {
              commentsToCreate.push({
                sequence_number: comment.sequence_number,
                text: comment.text.trim()
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
            } else if (comment.text.trim() === '') {// user erased the comment, presumably meaning to delete it
              commentsToDelete.push(comment.id);
            } else {
              commentsToUpdate.push({
                id: comment.id,
                sequence_number: comment.sequence_number,
                text: comment.text.trim()
              });
            }
          }
        }
      });

      console.log('comments to delete:', commentsToDelete);
      console.log('comments to comments update:', commentsToUpdate);
      console.log('comments to create:', commentsToCreate);
      console.log('comments to leave:', commentsToLeave);

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
                courseOfferingItem.manuallyMarkedOK = courseOfferingItem.delta === null ? false : courseOfferingItem.delta.manually_marked_OK;

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
      // one exception is if the delta object contains is of the "create" or "delete" type and it
      // contains a "note_to_self"; in that case, we don't delete the delta object, but instead change
      // it to the "no_action" type, so that we don't lose the notes;
      // at this point we don't bother deleting delta objects of the "update" variety, since all of their
      // properties can just be set to false, and then they basically don't do anything;
      // we also delete other DeltaCourseOffering objects of the "create", "delete" and "no_action" types, basically
      // to do some clean-up; otherwise, the next time the user loads the page, they may get inconsistent results (i.e.,
      // an older Delta object may show up again)
      let deltaAction = item.delta.requested_action; // need this later in order to know the appropriate way to refresh the page....
      let dataForPost = {
        deltaId: item.delta.id,
        iChairCourseOfferingId: item.hasIChair ? item.ichair.course_offering_id : null,
        crn: item.crn,
        semesterId: item.semesterId
      };
      $.ajax({
        // initialize an AJAX request
        type: "POST",
        url: "/planner/ajax/delete-delta/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(jsonResponse) {
          console.log("response: ", jsonResponse);
          item.delta = jsonResponse.delta_course_offering;
          item.manuallyMarkedOK = false;
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
      //  - DELTA_UPDATE_TYPE_MARK_OK (updateSetOrUnset is ignored in this case)
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
        case DELTA_UPDATE_TYPE_MARK_OK:
          deltaMods = {
            manuallyMarkedOK: item.manuallyMarkedOK
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
      // this method is used to generate a new delta object of requested_action "update" or "no_action" type, or to (confusingly) update an existing
      // delta object of any requested_action type ("update", "create", "delete" or "no_action");
      // creating a new delta object of requested_action "create" type is handled in another method; likewise for the "delete" type
      //
      // thus, if a delta object does not already exist in the item, we will generate a new one, with requested_action being "update" or "no_action"
      //
      // the delta object has information about what type delta "requested_action" type it is, if the delta object exists....
      // options for the requested action are:
      //  - DELTA_ACTION_CREATE
      //  - DELTA_ACTION_UPDATE
      //  - DELTA_ACTION_DELETE
      //  - DELTA_ACTION_NO_ACTION

      //WORKING HERE
      //DELTA_UPDATE_TYPE_MARK_OK = "manuallyMarkedOK";
      console.log(deltaMods);

      let dataForPost = {};
      if (item.delta !== null) {
        // there is an existing delta object, so we are updating that object; it can be of requested_action type "create", "update", "delete" or "no_action"
        if (item.delta.requested_action === DELTA_ACTION_UPDATE) {
          dataForPost = {
            deltaMods: deltaMods,
            deltaId: item.delta.id,
            action: item.delta.requested_action, // action we are requesting of the registrar
            crn: item.crn,
            campus: item.campus,
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
            campus: item.campus,
            iChairCourseOfferingId: item.ichair.course_offering_id,
            bannerCourseOfferingId: null, // no banner course offering exists, since we are requesting that the registrar create a new one
            semesterId: item.semesterId,
            includeRoomComparisons: item.includeRoomComparisons
          };
        } else if (item.delta.requested_action === DELTA_ACTION_NO_ACTION) {
          // in this case the delta object could have either a crn or an iChair course offering (although probably/hopefully not both)
          dataForPost = {
            deltaMods: deltaMods,
            deltaId: item.delta.id,
            action: item.delta.requested_action, // action we are requesting of the registrar
            crn: item.crn,
            campus: item.campus,
            iChairCourseOfferingId: item.hasIChair ? item.ichair.course_offering_id : null,
            bannerCourseOfferingId: item.hasBanner ? item.banner.course_offering_id : null,
            semesterId: item.semesterId,
            includeRoomComparisons: item.includeRoomComparisons
          };
        } else if (item.delta.requested_action === DELTA_ACTION_DELETE) {
          console.log("deleting!");
        } else {
          console.log("ERROR!!!  The requested action has not been recognized: ", item.delta.requested_action);
        }
      } else {
        // if there is no delta object, we are adding a new delta object, with requested_action (of the registrar) being "update" or "no_action"
        dataForPost = {
          deltaMods: deltaMods,
          deltaId: null,
          action: (item.hasIChair && item.hasBanner) ? DELTA_ACTION_UPDATE : DELTA_ACTION_NO_ACTION, // we reserve the "no action" setting for cases in which the item only has an ico or a bco, but not both
          crn: item.crn,
          campus: item.campus,
          iChairCourseOfferingId: item.hasIChair ? item.ichair.course_offering_id : null,
          bannerCourseOfferingId: item.hasBanner ? item.banner.course_offering_id : null,
          semesterId: item.semesterId,
          includeRoomComparisons: item.includeRoomComparisons
        };
      }

      console.log('data for post: ', dataForPost);

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
          item.manuallyMarkedOK = item.delta === null ? false : item.delta.manually_marked_OK;
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
          item.manuallyMarkedOK = item.delta === null ? false : item.delta.manually_marked_OK;
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
        //room: {
        //  id: NO_ROOM_SELECTED_ID,
        //  short_name: "-----",
        //  capacity: -1
        //},
        rooms: [{
          id: NO_ROOM_SELECTED_ID,
          short_name: "-----",
          inactive_after: null,
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
      this.editSemesterId = null;
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
        // https://www.w3schools.com/jsref/jsref_trim_string.asp
        meeting.begin_at = meeting.begin_at.trim();
        meeting.end_at = meeting.end_at.trim();
        if (meeting.id !== null && (meeting.delete === true || (meeting.begin_at === "" && meeting.end_at === "")))  {
          // if the user manually deletes both the start and end times, presumably they want to delete the meeting itself....
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
                courseOfferingItem.manuallyMarkedOK = courseOfferingItem.delta === null ? false : courseOfferingItem.delta.manually_marked_OK;
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
              campus: item.campus,
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

    generateExcel() {
      let courseData = [];
      this.courseOfferings.forEach(item => {
        if (item.delta !== null) {
          if (item.delta.messages_exist) {
            courseData.push({
              term_code: item.termCode,
              term_name: item.semester,
              crn: item.crn,
              campus: item.campus,
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
        url: "/planner/ajax/generate-excel/",
        dataType: "json",
        data: JSON.stringify(dataForPost),
        success: function(response) {
          //console.log("response: ", response);
          //console.log("response url", response.UUID);
          var url = '/planner/scheduleeditsexcel/'+response.UUID+'/';
          window.location = url;
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
      let otherUsedRoomIds = [];
      rooms.forEach( room => {
        if ((room.id !== roomId) && (room.id !== NO_ROOM_SELECTED_ID)) {
          otherUsedRoomIds.push(room.id);
        }
      });
      // need the semester start date so that we can filter out rooms that are no longer
      // active at the beginning of the semester....
      let semesterBeginOn;
      this.semesterChoices.forEach( semester => {
        if (semester.id === this.editSemesterId) {
          semesterBeginOn = new Date(semester.begin_on);
        }
      })

      let activeRoomsThisSemester = [];
      this.roomChoices.forEach( room => {
        if (room.inactive_after === null) {
          activeRoomsThisSemester.push(room);
        } else {
          let roomInactiveAfter = new Date(room.inactive_after);
          if (roomInactiveAfter >= semesterBeginOn) {
            // there is an "inactive_after" date set for the room, but it is after the start of this semester, so we can still use this room
            activeRoomsThisSemester.push(room);
          }
        }
      });
      //https://stackoverflow.com/questions/33577868/filter-array-not-in-another-array#:~:text=You%20can%20simply%20run%20through,when%20the%20callback%20returns%20true%20.
      return activeRoomsThisSemester.filter( roomOption => !otherUsedRoomIds.includes(roomOption.id));
    },

    addRoomToMeetingTime(rooms) {
      rooms.push({
        id: NO_ROOM_SELECTED_ID,
        capacity: -1,
        inactive_after: null,
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
    },

    registrarNoteIsStale(delta) {
      if (!delta.registrar_comment_exists) {
        return false;
      } else if (this.noPropertiesStagedForUpdate(delta)) {
        // there is a registrar comment, but no other properties are staged for an update at this point;
        // in this situation, users can become confused, because there could be an old note (from a previous edit, perhaps)
        // that they don't recall writing, and now it will end up on the schedule edits pdf....
        console.log('!!! possibly have a stale note....', delta);
        // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/now
        let now = Date.now()
        //delta = DeltaCourseOffering.objects.get(pk=co["delta"]["id"])
        // https://stackoverflow.com/questions/35300460/get-date-from-a-django-datetimefield
        //date_diff = now-delta.updated_at.date()
        let updatedAt = Date.parse(delta.updated_at);
        let oneDay = 24*60*60*1000; //one day in milliseconds
        console.log('now:', now);
        console.log('updatedAt:', updatedAt);
        let dateDiffDays = (now-updatedAt)/oneDay;
        console.log('diff:', dateDiffDays);
        return dateDiffDays >= 4;
      } else {
        return false;
      }
    },

    noPropertiesStagedForUpdate(delta) {
      //returns true if there are no properties that are staged for updates
      return (delta.meeting_times === null) &&
          (delta.instructors === null) &&
          (delta.semester_fraction === null) &&
          (delta.max_enrollment === null) &&
          (delta.delivery_method === null) &&
          (delta.public_comments === null) &&
          (delta.public_comments_summary === null)
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
    },
    staleMessages() {
      let messageArray = [];
      this.courseOfferings.forEach((courseOfferingItem) => {
        if (courseOfferingItem.delta !== null) {
          console.log('delta!', courseOfferingItem.delta);
          // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date#the_epoch_timestamps_and_invalid_date
          let updatedDate = new Date(Date.parse(courseOfferingItem.delta.updated_at));
          if (this.registrarNoteIsStale(courseOfferingItem.delta)) {
            messageArray.push({
              id: courseOfferingItem.delta.id,
              deltaUpdatedAt: updatedDate.toDateString(),
              text: courseOfferingItem.delta.registrar_comment,
              index: courseOfferingItem.index,
              crn: courseOfferingItem.crn,
              course: courseOfferingItem.course, 
              courseTitle: courseOfferingItem.name,
              semester: courseOfferingItem.semester
            });
          }
        }
      });
      return messageArray;
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

