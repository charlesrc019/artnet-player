<template>
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
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="recording in recordings"
          :key="recording.name"
          @click="startPlayback(recording.identifier)"
        >
          <td>{{ recording.name }}</td>
          <td>{{ recording.configuration }}</td>
          <td>
            {{ 
              String(Math.floor(recording.seconds / 60)) + 
              ":" + 
              (recording.seconds - (Math.floor(recording.seconds / 60) * 60)).toLocaleString('en-US', {minimumIntegerDigits: 2}) 
            }}
          </td>
        </tr>
      </tbody>
    </template>
  </v-simple-table>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      recordings: []
    }
  },
  methods: {
    startPlayback(identifier) {
      axios
        //.post("http://" + window.location.hostname + ":" + window.location.port + "/api/play?id=" + identifier)
        .post("http://10.0.0.7:8080/api/play?id=" + identifier)
        .then(response => {})
        .catch(error => {
          console.log(error)
        })
    }
  },
  mounted: function() {
    axios
      //.get("http://" + window.location.hostname + ":" + window.location.port + "/api/recordings")
      .get("http://10.0.0.7:8080/api/recordings")
      .then(response => {
        this.recordings = response.data
      })
      .catch(error => {
        console.log(error)
      })
  }
}
</script>
