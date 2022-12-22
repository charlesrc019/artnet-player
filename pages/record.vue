<template>
  <v-container>
    <v-card flat>
      <v-simple-table class="mt-4">
        <template v-slot:default>
          <thead>
            <tr>
              <th></th>
              <th class="text-left">
                Configuration Name
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
              <td>
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
          disabled
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
          Remove
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
  </v-container>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      selected: null,
      configurations: []
    }
  },
  methods: {
    recordPlayback() {
      axios
        //.post("http://" + window.location.hostname + ":" + window.location.port + "/api/record?id=" + this.selected)
        .post("http://10.0.0.7:8080/api/record?id=" + this.selected)
        .then(response => {})
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
            window.location.reload(true)
          })
          .catch(error => {
            console.log(error)
          })
      }
    }
  },
  mounted() {
    axios
      //.get("http://" + window.location.hostname + ":" + window.location.port + "/api/configurations")
      .get("http://10.0.0.7:8080/api/configurations")
      .then(response => {
        this.configurations = response.data
      })
      .catch(error => {
        console.log(error)
      })
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