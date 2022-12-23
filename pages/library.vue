<template>
  <v-container>
    <v-card>
      <v-card-title>
        Recordings
        <v-spacer></v-spacer>
        <v-text-field
          v-model="search"
          append-icon="mdi-magnify"
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
      >
        <template v-slot:item.actions="{ item }">
          <v-icon
            small
            class="mr-2"
            @click="playRecording(item)"
          >
            mdi-play
          </v-icon>
          <v-icon
            small
            class="mr-2"
            @click="insertRecording(item)"
          >
            mdi-page-next-outline
          </v-icon>
          <v-icon
            small
            class="mr-2"
            @click="addRecording(item)"
          >
            mdi-playlist-plus
          </v-icon>
          <v-icon
            small
            class="mr-2"
            @click="editRecording(item)"
          >
            mdi-pencil
          </v-icon>
          <v-icon
            small
            @click="deleteRecording(item)"
          >
            mdi-delete
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
            :rules="rules"
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
      search: "",
      headers: [
        {
          text: "Name",
          align: "start",
          sortable: true,
          groupable: false,
          value: "name"
        },
        {
          text: "Configuration",
          align: "start",
          sortable: true,
          value: "configuration"
        },
        {
          text: "Duration",
          align: "start",
          filterable: false,
          sortable: true,
          groupable: false,
          value: "duration"
        },
        {
          text: "Actions",
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
        //.get("http://" + window.location.hostname + ":" + window.location.port + "/api/recordings")
        .get("http://10.0.0.7:8080/api/recordings")
        .then(response => {
          this.recordings = response.data
        })
        .catch(error => {
          console.log(error)
        })
    },
    playRecording(item) {
      axios
        //.post("http://" + window.location.hostname + ":" + window.location.port + "/api/queue?when=now&id=" + identifier)
        .post("http://10.0.0.7:8080/api/queue?when=now&id=" + item.identifier)
        .then(response => {})
        .catch(error => {
          console.log(error)
        })
    },
    insertRecording(item) {
      axios
        //.post("http://" + window.location.hostname + ":" + window.location.port + "/api/queue?when=next&id=" + identifier)
        .post("http://10.0.0.7:8080/api/queue?when=next&id=" + item.identifier)
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
        //.post("http://" + window.location.hostname + ":" + window.location.port + "/api/queue?id=" + identifier)
        .post("http://10.0.0.7:8080/api/queue?id=" + item.identifier)
        .then(response => {
          this.snackbar_text = "Added to queue."
          this.snackbar = true
        })
        .catch(error => {
          console.log(error)
        })
    },
    editRecording(item) {
      axios
        //.post("http://" + window.location.hostname + ":" + window.location.port + "/api/queue?when=now&id=" + identifier)
        .post("http://10.0.0.7:8080/api/queue?when=now&id=" + item.identifier)
        .then(response => {})
        .catch(error => {
          console.log(error)
        })
    },
    deleteRecording(item) {
      if (confirm("This recording will be permanently deleted.\nContinue?")) {
        axios
          //.delete("http://" + window.location.hostname + ":" + window.location.port + "/api/queue?when=now&id=" + identifier)
          .delete("http://10.0.0.7:8080/api/recordings?id=" + item.identifier)
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
  mounted() {
    this.load()
  }
}
</script>
