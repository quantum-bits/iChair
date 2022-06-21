Vue.component("help-dialog", {
    template: `
        <div>
        <template>
            <div class="text-center">
                <v-dialog v-model="localHelpDialog" max-width="500">
                    <v-card>
                        <v-card-title class="headline grey lighten-2" primary-title>
                            Title!
                        </v-card-title>
                        <v-card-text class="pb-0">
                            <v-container grid-list-md>
                                <v-layout wrap>
                                    <v-flex xs12>
                                        Here is the message!
                                    </v-flex>
                                </v-layout>
                            </v-container>
                        </v-card-text>
                        <v-divider class="ma-0"></v-divider>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="primary">
                                Got it!
                            </v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>
            </div>
        </template>
            hi there

            [[ someLocalData ]]
        </div>
      `,
    delimiters: ["[[", "]]"],
    props: ["someData", "helpDialog"],
    data: function() {
      return {
        // https://stackoverflow.com/questions/40408096/whats-the-correct-way-to-pass-props-as-initial-data-in-vue-js-2
        someLocalData: this.someData,
        localHelpDialog: this.helpDialog
      }
    },
    methods: {
      
    },
    updated() {
      this.$nextTick(function () {
        console.log("help dialog updated: ", this.someData, this.helpDialog);
        this.someLocalData = this.someData;
        this.localHelpDialog = this.helpDialog;
        // Code that will run only after the
        // entire view has been re-rendered
      })
    },
    mounted: function() {
      console.log("help dialog mounted: ", this.someData, this.helpDialog);
    }
  });
  