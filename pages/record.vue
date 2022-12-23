<template>
  <v-container>
    <v-card flat>
      <v-simple-table class="mt-4">
        <template v-slot:default>
          <thead>
            <tr>
              <th></th>
              <th class="text-left">
                Configuration
              </th>
              <th class="text-left">
                Created On
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="configuration in configurations"
              :key="configuration.name"
            >
              <td align="start">
                <v-radio-group v-model="selected">
                  <v-radio class="table-radio ma-0 pa-0" :value="configuration.name"/>
                </v-radio-group>
              </td>
              <td>{{ configuration.name }}</td>
              <td>{{ configuration.created }}</td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
      <v-row class="px-3 pt-6">
        <v-btn
          class="ma-2"
          color="secondary"
          large
          @click.stop="dialog = true"
        >
          Add
        </v-btn>
        <v-btn
          class="my-2"
          color="secondary"
          large
          :disabled="selected == null"
          @click="deleteConfiguration()"
        >
          Delete
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          class="ma-2"
          color="red"
          large
          :disabled="selected == null"
          @click="recordPlayback()"
        >
          Record
        </v-btn>
      </v-row>
    </v-card>
    <v-dialog
      v-model="dialog"
      max-width="360"
    >
      <v-card>
        <v-card-title class="text-h5">
          Add Configuration
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
            @click="addConfiguration()"
          >
            Add
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
      selected: null,
      dialog: false,
      dialog_text: "",
      configurations: [],
      rules: [
        value => !!value || 'Required.',
        value => (value && value.length >= 3) || 'Min 3 characters.',
      ],
      snackbar: false,
      snackbar_text: ""
    }
  },
  methods: {
    load() {
      axios
        //.get("http://" + window.location.hostname + ":" + window.location.port + "/api/configurations")
        .get("http://10.0.0.7:8080/api/configurations")
        .then(response => {
          this.configurations = response.data
        })
        .catch(error => {
          console.log(error)
        })
    },
    recordPlayback() {
      axios
        //.post("http://" + window.location.hostname + ":" + window.location.port + "/api/record?id=" + this.selected)
        .post("http://10.0.0.7:8080/api/record?id=" + this.selected)
        .then(response => {})
        .catch(error => {
          console.log(error)
        })
    },
    addConfiguration() {
      axios
        //.delete("http://" + window.location.hostname + ":" + window.location.port + "/api/configurations?name=" + this.dialog_text)
        .post("http://10.0.0.7:8080/api/configurations?name=" + this.dialog_text)
        .then(response => {
          this.dialog = false
          this.snackbar = true
          this.snackbar_text = "Configuration added."
          this.load()
        })
        .catch(error => {
          console.log(error)
        })
    },
    deleteConfiguration() {
      if (confirm("All associated recordings will be permanently deleted.\nContinue?")) {
        axios
          //.delete("http://" + window.location.hostname + ":" + window.location.port + "/api/configurations/" + this.selected)
          .delete("http://10.0.0.7:8080/api/configurations/" + this.selected)
          .then(response => {
            this.snackbar = true
            this.snackbar_text = "Configuration deleted."
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

<style>
  td .v-input,
  .v-input__slot {
    margin: 5px 0 0 0 !important;
  }
  .table-radio i {
    font-size: 18px !important;
  }
</style>