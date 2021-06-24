/*
some of the following code was adapted from code written by Tom Nurkkala
*/

Vue.component("room-picker", {
  template: `
    <div>
      <!-- https://stackoverflow.com/questions/43839066/how-can-i-set-selected-option-selected-in-vue-js-2 -->
      <select style="width: 50%;"
        :id="room.idForLabel"
        :name="room.idForLabel" 
        v-model="selectedRoomId"
        @change="selectionChanged">
        <option v-for="availableRoom in availableRooms" :value="availableRoom.id" :key="availableRoom.id">
            [[availableRoom.name]]
        </option>
      </select>
      <div v-if="index == 0" style="float: right;">
        <a class="btn btn-info" @click="addRoom" style="width: 80px;">
          Add Room</a>
      </div>
      <div v-else style="float: right;">
        <a class="btn btn-warning" @click="dropRoom" style="width: 80px;">
          Drop Room</a>
      </div>
    </div>
    `,
  delimiters: ["[[", "]]"],
  props: ["availableRooms", "room", "index"],
  data: function() {
    return {
      // https://stackoverflow.com/questions/40408096/whats-the-correct-way-to-pass-props-as-initial-data-in-vue-js-2
      selectedRoomId: this.room.id,
    }
  },
  methods: {
    selectionChanged() {
      this.$emit('roomChanged', this.room, this.selectedRoomId);
    },
    addRoom() {
      this.$emit('addRoom');
    },
    dropRoom() {
      this.$emit('dropRoom', this.room);
    }
  },
  updated() {
    this.$nextTick(function () {
      //console.log("room picker updated: ", this.room.id, this.selectedRoomId);
      this.selectedRoomId = this.room.id;
      // Code that will run only after the
      // entire view has been re-rendered
    })
  },
  mounted: function() {
    //console.log("room picker mounted: ", this.room.id, this.selectedRoomId);
  }
});

Vue.component("rooms-container", {
  template: `
    <div>
      <room-picker v-for="(room, index) in roomData" 
        :key="index" 
        :index="index"
        :availableRooms="filteredRoomChoices(room.id)" 
        :room="room"
        @roomChanged="roomChanged"
        @addRoom="addRoom"
        @dropRoom="dropRoom"></room-picker>
    </div>
    `,
  delimiters: ["[[", "]]"],
  props: ["initialRoomIds", "allRooms", "scheduledClassCounter", "noRoomSelectedId", "baseIdsForLabel"],
  data: function() {
    return {
      // https://stackoverflow.com/questions/40408096/whats-the-correct-way-to-pass-props-as-initial-data-in-vue-js-2
      // https://stackoverflow.com/questions/10270351/how-to-write-an-inline-if-statement-in-javascript
      roomData: [],
    }
  },
  methods: {
    filteredRoomChoices(roomId) {
      let otherUsedRoomIds = [];
      this.roomData.forEach( room => {
        if ((room.id !== roomId) && (room.id !== this.noRoomSelectedId)) {
          otherUsedRoomIds.push(room.id);
        }
      });
      //https://stackoverflow.com/questions/33577868/filter-array-not-in-another-array#:~:text=You%20can%20simply%20run%20through,when%20the%20callback%20returns%20true%20.
      return this.allRooms.filter( roomOption => !otherUsedRoomIds.includes(roomOption.id));
    },
    // https://medium.com/js-dojo/component-communication-in-vue-js-ca8b591d7efa
    roomChanged(changedRoom, newRoomId) {
      //console.log('message received!', changedRoom, newRoomId);
      let roomIndex = changedRoom.index;
      this.roomData.forEach( room => {
        if (room.index == roomIndex) {
          //console.log('found the room!', room);
          room.id = newRoomId;
        }
      });
      // https://medium.com/@miladmeidanshahi/update-array-and-object-in-vuejs-a283983fe5ba
      // the following is used so that vue/javascript picks up the change
      //Vue.set(this.selectedRoomIds, roomSelectorIndex, newRoomId)
    },
    addRoom() {
      //console.log('time to add a room!');
      let largestIndex = -1;
      this.roomData.forEach( room => {
        if (room.index > largestIndex) {
          largestIndex = room.index;
        }
      });
      let index = largestIndex + 1;
      this.roomData.push({
        id: this.noRoomSelectedId,
        index: index,
        idForLabel: this.baseIdsForLabel[this.scheduledClassCounter] + '-' +index.toString()
        });
    },
    dropRoom(roomToDrop) {
      //console.log('drop this room!', roomToDrop);
      let counter = 0;
      let roomDataIndexToDrop;
      this.roomData.forEach( room => {
        if (room.index === roomToDrop.index) {
          roomDataIndexToDrop = counter;
        }
        counter += 1;
      });
      //console.log('found the index: ', roomDataIndexToDrop);
      this.roomData.splice(roomDataIndexToDrop, 1);
    },
  },
  mounted: function () {
    // https://vuejs.org/v2/api/#mounted
    // Code that will run only after the
    // entire view has been rendered
    
    //console.log('inside mounted');
    this.roomData = [];
    let counter = 0;
    if (this.initialRoomIds.length === 0) {
      this.roomData.push({
        id: this.noRoomSelectedId,
        index: counter,
        idForLabel: this.baseIdsForLabel[this.scheduledClassCounter] + '-' +counter.toString()
      });
    } else {
      this.initialRoomIds.forEach( roomId => {
        this.roomData.push({
          id: roomId,
          index: counter,
          idForLabel: this.baseIdsForLabel[this.scheduledClassCounter] + '-' +counter.toString()
        });
        counter += 1;
      });
    
      //console.log('roomData: ', this.roomData);
    }
  }
  
});

// The following is adapted from code written by Tom Nurkkala.
// "Top-level" Vue component that will associate itself with the `#app` div.
new Vue({
    delimiters: ["[[", "]]"],
    name: "class-schedule-form", // This shows up in the Vue debugger.
    el: "#app", // DOM element to take over
    data: {
        // Local data value, just for illustration. (KK: the following is not used anymore....)
        //message: "Pick a room, ... any room.",
        // Access static data from the server, defined in the top-level `<script>` tag.
        //days: dayData,
        //rooms: json_data.rooms,
        //rowData: json_data.row_data
    },
});