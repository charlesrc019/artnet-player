<template>
  <v-container>
    <v-card flat>
      <v-card-title class="pl-6">
        Configurations
      </v-card-title>
      <v-simple-table class="mt-4">
        <template v-slot:default>
          <thead>
            <tr>
              <th class="text-left">
                Configuration
              </th>
              <th class="text-left d-none d-md-table-cell">
                Created On
              </th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="configuration in configurations"
              :key="configuration.name"
              @click.stop="selected = configuration.name"
            >
              <td>{{ configuration.name }}</td>
              <td class="d-none d-md-table-cell">{{ configuration.created }}</td>
              <td class="table-radio-cell">
                <v-radio-group v-model="selected">
                  <v-radio 
                    class="table-radio ma-0 pa-0" 
                    :value="configuration.name"
                    :on-icon="'radio_button_on'"
                    :off-icon="'radio_button_off'"
                  />
                </v-radio-group>
              </td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
      <v-row class="px-3 pt-6">
        <v-btn
          class="ma-2"
          color="secondary"
          @click.stop="dialog = true"
        >
          Add
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          class="my-2"
          color="secondary"
          :disabled="selected == null"
          @click="deleteConfiguration()"
        >
          Delete
        </v-btn>
        <v-btn
          class="ma-2"
          color="red"
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
        .get("http://" + this.$config.api + "/configurations")
        .then(response => {
          this.configurations = response.data
        })
        .catch(error => {
          console.log(error)
        })
    },
    recordPlayback() {
      axios
        .post("http://" + this.$config.api + "/record?id=" + this.selected)
        .then(response => {})
        .catch(error => {
          console.log(error.response)
          this.snackbar = true
          this.snackbar_text = "Unable to record."
        })
    },
    addConfiguration() {
      axios
        .post("http://" + this.$config.api + "/configurations?name=" + this.dialog_text)
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
          .delete("http://" + this.$config.api + "/configurations/" + this.selected)
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
  created() {
    this.load()
  }
}
</script>

<style>
  .table-radio i {
    font-size: 20px !important;
  }
  .table-radio-cell {
    max-width: 65px !important;
    width: 65px !important;
  }
</style>