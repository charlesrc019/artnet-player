<template>
  <v-container>
    <v-card flat>
      <v-card-title class="pl-6">
        Library
        <v-spacer></v-spacer>
        <v-text-field
          v-model="search"
          class="ma-0"
          append-icon="search"
          label="Search"
          single-line
          hide-details
        ></v-text-field>
      </v-card-title>
      <v-data-table
        :headers="headers"
        :items="recordings"
        item-key="name"
        class="elevation-1"
        :search="search"
        show-group-by
        hide-default-footer
        disable-pagination
      >
        <template v-slot:item.actions="{ item }">
          <!--<v-icon
            small
            class="mr-1"
            @click="playRecording(item)"
          >
            play_arrow
          </v-icon>
          <v-icon
            small
            class="mr-1"
            @click="insertRecording(item)"
          >
            keyboard_double_arrow_right
          </v-icon>-->
          <v-icon
            small
            class="mr-5"
            @click="addRecording(item)"
          >
            add
          </v-icon>
          <v-icon
            small
            class="mr-5"
            @click="loadDialog(item)"
          >
            mode_edit
          </v-icon>
          <v-icon
            small
            @click="deleteRecording(item)"
          >
            delete
          </v-icon>
        </template>
      </v-data-table>
    </v-card>
        <v-dialog
      v-model="dialog"
      max-width="360"
    >
      <v-card>
        <v-card-title class="text-h5">
          Edit Recording
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="dialog_text"
            label="Name"
            hide-details="auto"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            class="my-2"
            color="secondary"
            text
            @click="dialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            class="my-2"
            color="primary"
            text
            @click="editRecording()"
          >
            Edit
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-snackbar
      v-model="snackbar"
      :timeout=1000
    >
      {{ snackbar_text }}
      <template v-slot:action="{ attrs }">
        <v-btn
          color="primary"
          text
          v-bind="attrs"
          @click="snackbar = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      api: window.location.hostname + ":" + window.location.port + "/api",
      search: "",
      headers: [
        {
          text: "Sequence",
          align: "start",
          sortable: true,
          groupable: false,
          value: "name"
        },
        {
          text: "Configuration ",
          align: "start",
          sortable: true,
          value: "configuration"
        },
        //{
        //  text: "Duration",
        //  align: "start",
        //  filterable: false,
        //  sortable: true,
        //  groupable: false,
        //  value: "duration"
        //},
        {
          text: "",
          align: "center",
          filterable: false,
          sortable: false,
          groupable: false,
          value: "actions"
        }
      ],
      recordings: [],
      snackbar: false,
      snackbar_text: "",
      dialog: false,
      dialog_id: "",
      dialog_text: "",
    }
  },
  methods: {
    load() {
      axios
        .get("http://" + this.api + "/recordings")
        .then(response => {
          this.recordings = response.data
        })
        .catch(error => {
          console.log(error)
        })
    },
    loadDialog(item) {
      this.dialog_id = item.identifier
      this.dialog_text = item.name
      this.dialog = true
    },
    playRecording(item) {
      axios
        .post("http://" + this.api + "/playback?when=now&id=" + item.identifier)
        .then(response => {})
        .catch(error => {
          console.log(error)
        })
    },
    insertRecording(item) {
      axios
        .post("http://" + this.api + "/playback?when=next&id=" + item.identifier)
        .then(response => {
          this.snackbar_text = "Added to queue next."
          this.snackbar = true
        })
        .catch(error => {
          console.log(error)
        })
    },
    addRecording(item) {
      axios
        .post("http://" + this.api + "/playback?id=" + item.identifier)
        .then(response => {
          this.snackbar_text = "Added to queue."
          this.snackbar = true
        })
        .catch(error => {
          console.log(error)
        })
    },
    editRecording() {
      axios
        .put("http://" + this.api + "/recordings/" + this.dialog_id + "?name=" + encodeURIComponent(this.dialog_text))
        .then(response => {
          this.dialog = false
          this.snackbar_text = "Recording edited."
          this.snackbar = true
          this.load()
        })
        .catch(error => {
          console.log(error)
        })
    },
    deleteRecording(item) {
      if (confirm("This recording will be permanently deleted.\nContinue?")) {
        axios
          .delete("http://" + this.api + "/recordings/" + item.identifier)
          .then(response => {
            this.snackbar_text = "Recording deleted."
            this.snackbar = true
            this.load()
          })
          .catch(error => {
            console.log(error)
          })
      }
    }
  },
  created() {
    if (this.$config.dev_endpoint !== "") {
      this.api = this.$config.dev_endpoint
    }
    this.load()
  }
}
</script>
