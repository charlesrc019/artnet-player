<template>
  <v-container>
    <v-card flat>
      <v-card-title class="pl-6">
        Queue
      </v-card-title>
      <v-simple-table class="mt-4">
        <template v-slot:default>
          <thead>
            <tr>
              <th class="text-left">
                Name
              </th>
              <th class="text-left d-none d-lg-table-cell">
                Configuration
              </th>
              <th class="text-left d-none d-lg-table-cell">
                Duration
              </th>
              <th class="text-left table-action-cell">
                Repeat
              </th>
              <th class="text-center table-action-cell">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in items"
              :key="item.name"
            >
              <td>{{ item.name }}</td>
              <td class="d-none d-lg-table-cell">{{ item.configuration }}</td>
              <td class="d-none d-lg-table-cell">
                {{ 
                  String(Math.floor(item.total_secs / 60)) + 
                  ":" + 
                  (item.total_secs - (Math.floor(item.total_secs / 60) * 60)).toLocaleString('en-US', {minimumIntegerDigits: 2}) 
                }}
              </td>
              <td class="table-action-cell">
                <v-checkbox
                  v-model="item.is_looped"
                  @click="loopItem(item.position, item.is_looped)"
                >
                </v-checkbox>
              </td>
              <td class="text-center table-action-cell">
                <v-icon
                  small
                  class="mr-2"
                  @click="prioritizeItem(item.position)"
                >
                  mdi-chevron-up
                </v-icon>
                <v-icon
                  small
                  class="mr-2"
                  @click="moveItem(item.position)"
                >
                  mdi-chevron-triple-up
                </v-icon>
                <v-icon
                  small
                  class="mr-2"
                  @click="deleteItem(item.position)"
                >
                  mdi-delete
                </v-icon>
              </td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
    </v-card>
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
      items: [],
      interval: "",
      snackbar: false,
      snackbar_text: "",
    }
  },
  methods: {
    load() {
      axios
        //.get("http://" + window.location.hostname + ":" + window.location.port + "/api/playback")
        .get("http://10.0.0.21:8080/api/playback")
        .then(response => {
          this.items = response.data.items
        })
        .catch(error => {
          console.log(error)
        })
    },
    moveItem(pos) {
      axios
        //.put("http://" + window.location.hostname + ":" + window.location.port + "/api/playback/" + pos)
        .put("http://10.0.0.21:8080/api/playback/" + pos + "?position=up")
        .then(response => {
          this.snackbar_text = "Item moved."
          this.snackbar = true
        })
        .catch(error => {
          console.log(error)
        })
    },
    prioritizeItem(pos) {
      axios
        //.put("http://" + window.location.hostname + ":" + window.location.port + "/api/playback/" + pos)
        .put("http://10.0.0.21:8080/api/playback/" + pos + "?position=next")
        .then(response => {
          this.snackbar_text = "Item moved next."
          this.snackbar = true
        })
        .catch(error => {
          console.log(error)
        })
    },
    loopItem(pos, is_looped) {
      var loop_txt = "true"
      if (!is_looped) {
        loop_txt = "false"
      }
      axios
        //.put("http://" + window.location.hostname + ":" + window.location.port + "/api/playback/" + pos)
        .put("http://10.0.0.21:8080/api/playback/" + pos + "?loop=" + loop_txt)
        .then(response => {
          this.snackbar_text = "Item looped."
          if (!is_looped) {
            this.snackbar_text = "Item unlooped."
          }
          this.snackbar = true
        })
        .catch(error => {
          console.log(error)
        })
    },
    deleteItem(pos) {
      axios
        //.delete("http://" + window.location.hostname + ":" + window.location.port + "/api/playback/" + pos)
        .delete("http://10.0.0.21:8080/api/playback/" + pos)
        .then(response => {
          this.snackbar_text = "Item deleted."
          this.snackbar = true
        })
        .catch(error => {
          console.log(error)
        })
    }
  },
  mounted() {
    this.load()
    this.interval = setInterval(this.load, 2000)
  },
  beforeUnmount() {
    clearInterval(this.interval)
  },
  destroyed() {
    clearInterval(this.interval)
  }
}
</script>

<style>
  .table-action-cell {
    max-width: 45px !important;
  }
</style>