<template>
  <v-container>
    <v-card class="mb-6" flat>
      <v-card-title class="pl-6">
        Queue
      </v-card-title>
      <v-simple-table class="mt-4">
        <template v-slot:default>
          <thead>
            <tr>
              <th class="text-left">
                Sequence
              </th>
              <th class="text-left d-none d-md-table-cell">
                Duration
              </th>
              <th class="text-left table-check-cell">
                Loop
              </th>
              <th class="text-center table-action-cell"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in items"
              :key="item.position"
            >
              <td :color="(item.position === 0) ? '#777' : '#fff'">{{ item.name }}</td>
              <td 
                class="d-none d-md-table-cell"
                :color="(item.position === 0) ? '#777' : '#fff'"
              >
                {{ 
                  String(Math.floor(item.total_secs / 60)) + 
                  ":" + 
                  (item.total_secs - (Math.floor(item.total_secs / 60) * 60)).toLocaleString('en-US', {minimumIntegerDigits: 2}) 
                }}
              </td>
              <td class="table-check-cell">
                <v-checkbox
                  class="table-check"
                  v-model="item.is_looped"
                  :on-icon="'repeat'"
                  :off-icon="'arrow_right_alt'"
                  @click="loopItem(item.position, item.is_looped)"
                >
                </v-checkbox>
              </td>
              <td class="text-center table-action-cell">
                <v-icon
                  small
                  class="mr-1"
                  @click="prioritizeItem(item.position)"
                  v-if="(item.position <= 1) ? false : true"
                >
                  keyboard_arrow_up
                </v-icon>
                <v-icon
                  small
                  class="mr-1"
                  @click="moveItem(item.position)"
                  v-if="(item.position <= 1) ? false : true"
                >
                  keyboard_double_arrow_up
                </v-icon>
                <v-icon
                  small
                  class="mr-1"
                  @click="deleteItem(item.position)"
                  v-if="(item.position === 0) ? false : true"
                >
                  delete
                </v-icon>
              </td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
    </v-card>
    <v-card flat>
      <v-card-title class="pl-6">
        Standby
        <v-spacer></v-spacer>
        <v-select
          :items="sequences"
          item-title="name"
          item-value="identifier"
          label="Sequence"
          single-line
        ></v-select>
      </v-card-title>
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
      api: window.location.hostname + ":" + window.location.port + "/api",
      items: [],
      interval: "",
      snackbar: false,
      snackbar_text: "",
      sequences: []
    }
  },
  methods: {
    load() {
      axios
        .get("http://" + this.api + "/playback")
        .then(response => {
          this.items = response.data.items
        })
        .catch(error => {
          console.log(error)
        })
    },
    load_standby() {
      axios
        .get("http://" + this.api + "/playback/standby")
        .then(response => {
          console.log(response.data)
          this.sequences = response.data.sequences
          this.standby = response.data.standby
        })
        .catch(error => {
          console.log(error)
        })
    },
    moveItem(pos) {
      axios
        .put("http://" + this.api + "/playback/" + pos + "?position=up")
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
        .put("http://" + this.api + "/playback/" + pos + "?position=next")
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
        .put("http://" + this.api + "/playback/" + pos + "?loop=" + loop_txt)
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
        .delete("http://" + this.api + "/playback/" + pos)
        .then(response => {
          this.snackbar_text = "Item deleted."
          this.snackbar = true
        })
        .catch(error => {
          console.log(error)
        })
    }
  },
  created() {
    if (this.$config.dev_endpoint !== "") {
      this.api = this.$config.dev_endpoint
    }
    this.load()
    this.load_standby()
    this.interval = setInterval(this.load, 500)
  },
  destroyed() {
    clearInterval(this.interval)
  }
}
</script>

<style>
  .table-action-cell {
    max-width: 100px !important;
    width: 100px !important;
  }
  .table-check-cell {
    max-width: 70px !important;
    width: 70px !important;
  }
  .table-check-cell i {
    font-size: 20px !important;
  }
</style>