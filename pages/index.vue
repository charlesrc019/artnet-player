<template>
  <v-simple-table>
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
        >
          <td>{{ recording.name }}</td>
          <td>{{ recording.configuration }}</td>
          <td>{{ item.seconds }}</td>
        </tr>
      </tbody>
    </template>
  </v-simple-table>
</template>

<script>
import axios from 'axios'
export default {
  data () {
    return {
      recordings: []
    }
  },
  mounted () {
  axios
    //.get("http://" + window.location.hostname + ":" + window.location.port + "/recordings")
    .get("http://10.0.0.5/recordings")
    .then(response => {
      this.recordings = response
    })
    .catch(error => {
      console.log(error)
    })
  }
}
</script>
