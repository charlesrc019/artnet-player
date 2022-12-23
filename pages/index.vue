<template>
  <v-container>
    <v-card>
      <v-card-title>
        Queue
      </v-card-title>
      <v-simple-table class="mt-4">
        <template v-slot:default>
          <thead>
            <tr>
              <th class="text-left">
                Name
              </th>
              <th class="text-left">
                Configuration
              </th>
              <th class="text-left">
                Duration
              </th>
              <th class="text-left">
                Repeat
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in items"
              :key="item.name"
            >
              <td>{{ item.name }}</td>
              <td>{{ item.configuration }}</td>
              <td>
                {{ 
                  String(Math.floor(item.total_secs / 60)) + 
                  ":" + 
                  (item.total_secs - (Math.floor(item.total_secs / 60) * 60)).toLocaleString('en-US', {minimumIntegerDigits: 2}) 
                }}
              </td>
              <td>
                <v-checkbox
                  v-model="item.is_looped"
                >
                </v-checkbox>
              </td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
    </v-card>
  </v-container>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      items: []
    }
  },
  methods: {
    load() {
      axios
        //.get("http://" + window.location.hostname + ":" + window.location.port + "/api/playback")
        .get("http://10.0.0.7:8080/api/playback")
        .then(response => {
          this.items = response.data.items
        })
        .catch(error => {
          console.log(error)
        })
    },
    deleteItem(pos) {
      axios
        //.post("http://" + window.location.hostname + ":" + window.location.port + "/api/playback/" + pos)
        .delete("http://10.0.0.7:8080/api/playback/" + pos)
        .then(response => {})
        .catch(error => {
          console.log(error)
        })
    }
  },
  load() {
    this.load()
  }
}
</script>
