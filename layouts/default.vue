<template>
  <v-app dark>
    <v-navigation-drawer
      v-model="drawer"
      fixed
      app
    >
      <v-list>
        <v-list-item
          v-for="(item, i) in items"
          :key="i"
          :to="item.to"
          router
          exact
        >
          <v-list-item-action>
            <v-icon>{{ item.icon }}</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title v-text="item.title" />
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
    <v-app-bar
      color="primary"
      fixed
      app
    >
      <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
      <v-toolbar-title v-text="title" />
      <v-spacer />
    </v-app-bar>
    <v-main>
      <v-container class="py-6">
        <Nuxt />
      </v-container>
    </v-main>
    <v-footer
      dark
      padless
      v-if="footer_visible"
    >
      <v-card
        color="secondary"
        class="flex"
        flat
        tile
      >
        <v-card-title class="px-8 pt-6 pb-0">
          <strong v-text="footer_title"></strong>
          <v-spacer></v-spacer>
          <v-btn
            dark
            icon
            @click="stopPlayback()"
          >
            <v-icon size="24px">mdi-stop</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text class="px-8 pt-2 pb-7 white--text text-left">
          {{ footer_row1 }} <br />
          {{ footer_row2 }}
        </v-card-text>

      </v-card>
    </v-footer>
  </v-app>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      title: 'ArtNet Player',
      drawer: false,
      footer_visible: false,
      footer_title: "",
      footer_row1: "",
      footer_row2: "",
      items: [
        {
          icon: 'mdi-magnify',
          title: 'Library',
          to: '/'
        },
        {
          icon: 'mdi-tray-full',
          title: 'Queue',
          to: '/queue'
        },
        {
          icon: 'mdi-plus-circle-outline',
          title: 'Record',
          to: '/record'
        }
      ],
      activity: {
        "status": "free"
      }
    }
  },
  methods: {
    stopPlayback() {
      axios
        //.post("http://" + window.location.hostname + ":" + window.location.port + "/api/stop")
        .post("http://10.0.0.26:8080/api/stop")
        .then(response => {})
        .catch(error => {
          console.log(error)
        })
    }
  },
  mounted: function() {
    //let socket = new WebSocket("ws://" + window.location.hostname + ":" + window.location.port + "/api/status")
    let socket = new WebSocket("ws://10.0.0.26/api/status")
    socket.onopen = (event) => {}
    socket.onmessage = (event) => {
      this.activity = JSON.parse(event.data)
      if (this.activity.status != "free") {
        this.footer_visible = true
        this.footer_title = this.activity.status.charAt(0).toUpperCase() + this.activity.status.slice(1) + "..."
        this.footer_row1 = this.activity.details.name
        this.footer_row2 = 
          String(Math.floor(this.activity.elasped_secs / 60)) + 
          ":" + 
          (this.activity.elasped_secs - (Math.floor(this.activity.elasped_secs / 60) * 60)).toLocaleString('en-US', {minimumIntegerDigits: 2})
        if (this.activity.status == "playing") {
          this.footer_row2 = 
            String(Math.floor(this.activity.elasped_secs / 60)) + 
            ":" + 
            (this.activity.elasped_secs - (Math.floor(this.activity.elasped_secs / 60) * 60)).toLocaleString('en-US', {minimumIntegerDigits: 2}) +
            " / " +
            String(Math.floor(this.activity.details.total_secs / 60)) + 
            ":" + 
            (this.activity.details.total_secs - (Math.floor(this.activity.details.total_secs / 60) * 60)).toLocaleString('en-US', {minimumIntegerDigits: 2})
        }
      }
      else {
        this.footer_visible = false
      }
    }
  }
}
</script>
