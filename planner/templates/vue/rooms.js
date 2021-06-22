Vue.component("day-picker", {
    template: `
      <div>
        <label :for="day.id">Choose Room for [[day.name]]</label>
        <select id="day.id" :name="day.id">
          <option v-for="room in day.rooms" :value="room.id" :key="room.id">
              [[room.name]]
          </option>
        </select>
      </div>
      `,
    delimiters: ["[[", "]]"],
    props: ["day"],
});

Vue.component("room-picker", {
  template: `
    <div>
      <!-- https://stackoverflow.com/questions/43839066/how-can-i-set-selected-option-selected-in-vue-js-2 -->
      <select id="selectId" style="width: 50%;"
        :name="selectId" 
        v-model="selectedRoomId"
        @change="selectionChanged">
        <option v-for="room in availableRooms" :value="room.id" :key="room.id">
            [[room.name]]
        </option>
      </select>
      <div v-if="index == 0" style="float: right;">
        <a class="btn btn-info" @click="addRoom">
                        Add Room</a>
      </div>
    </div>
    `,
  delimiters: ["[[", "]]"],
  props: ["availableRooms", "initialRoomId", "index", "scheduledClassId", "scheduledClassCounter"],
  data: function() {
    return {
      // https://stackoverflow.com/questions/40408096/whats-the-correct-way-to-pass-props-as-initial-data-in-vue-js-2
      selectedRoomId: this.initialRoomId,
    }
  },
  methods: {
    selectionChanged() {
      this.$emit('roomChanged', this.index, this.selectedRoomId);
    },
    addRoom() {
      this.$emit('addRoom');
    }
  },
  computed: {
    selectId() {
      return 'room-picker-'+this.scheduledClassCounter.toString()+'-'+this.index.toString();
    }
  }
});

Vue.component("rooms-container", {
  template: `
    <div>
      [[selectedRoomIds]] [[scheduledClassId]]
      <div>
        <room-picker v-for="(roomId, index) in selectedRoomIds" 
          :key="index" 
          :availableRooms="filteredRoomChoices(roomId)" 
          :initialRoomId="roomId" 
          :index="index"
          :scheduledClassId="scheduledClassId"
          :scheduledClassCounter="scheduledClassCounter"
          @roomChanged="roomChanged"
          @addRoom="addRoom"></room-picker>
      </div>
    </div>
    `,
  delimiters: ["[[", "]]"],
  props: ["initialRoomIds", "scheduledClassId", "allRooms", "scheduledClassCounter", "noRoomSelectedId"],
  data: function() {
    return {
      // https://stackoverflow.com/questions/40408096/whats-the-correct-way-to-pass-props-as-initial-data-in-vue-js-2
      // https://stackoverflow.com/questions/10270351/how-to-write-an-inline-if-statement-in-javascript
      selectedRoomIds: (this.initialRoomIds.length === 0 ? [this.noRoomSelectedId] : this.initialRoomIds),
    }
  },
  methods: {
    filteredRoomChoices(roomId) {
      let otherUsedRoomIds = [];
      this.selectedRoomIds.forEach( selectedRoomId => {
        if ((selectedRoomId !== roomId) && (selectedRoomId !== this.noRoomSelectedId)) {
          otherUsedRoomIds.push(selectedRoomId);
        }
      });
      //https://stackoverflow.com/questions/33577868/filter-array-not-in-another-array#:~:text=You%20can%20simply%20run%20through,when%20the%20callback%20returns%20true%20.
      return this.allRooms.filter( roomOption => !otherUsedRoomIds.includes(roomOption.id));
    },
    // https://medium.com/js-dojo/component-communication-in-vue-js-ca8b591d7efa
    roomChanged(roomSelectorIndex, newRoomId) {
      console.log('message received!', roomSelectorIndex, newRoomId);
      // https://medium.com/@miladmeidanshahi/update-array-and-object-in-vuejs-a283983fe5ba
      // the following is used so that vue/javascript picks up the change
      Vue.set(this.selectedRoomIds, roomSelectorIndex, newRoomId)
    },
    addRoom() {
      console.log('time to add a room!');
      this.selectedRoomIds.push(this.noRoomSelectedId);
    }
  },
  watch: {
    selectedRoomIds: {
      deep: true,
      handler(val) {
        console.log('room list changed', val);
      }
    },
  },
  computed: {
  }
});


// "Top-level" Vue component that will associate itself with the `#alpha` div.
new Vue({
    delimiters: ["[[", "]]"],
    name: "class-schedule-form", // This shows up in the Vue debugger.
    el: "#app", // DOM element to take over
    data: {
        // Local data value, just for illustration.
        message: "Pick a room, ... any room.",
        // Access static data from the server, defined in the top-level `<script>` tag.
        days: dayData,
        //rooms: json_data.rooms,
        //rowData: json_data.row_data
    },
});