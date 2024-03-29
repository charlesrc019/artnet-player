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
      <v-app-bar-nav-icon 
        @click.stop="drawer = !drawer" 
        :disabled="!drawer_changeable"
      >
        <v-icon>menu</v-icon>
      </v-app-bar-nav-icon>
      <v-toolbar-title v-text="title" />
      <v-spacer />
    </v-app-bar>
    <v-main>
      <v-container class="py-6">
        <v-card
          color="accent"
          class="flex mx-3 mb-2 px-4 py-2"
          flat
          tile
        >
          <v-card-title class="pb-0">
            <strong v-text="footer_title"></strong>
            <v-spacer></v-spacer>
            <v-btn
              dark
              icon
              @click="stopPlayback()"
            >
              <v-icon color="red" size="30px" v-show="footer_visible">stop</v-icon>
            </v-btn>
          </v-card-title>

          <v-card-text class="mb-1 white--text text-left">
            {{ footer_row1 }} <br />
            {{ footer_row2 }}
          </v-card-text>

          <div class="expanding-div"></div>

        </v-card>
        <Nuxt />
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      api: window.location.hostname + ":" + window.location.port + "/api",
      title: 'ArtNet Player',
      drawer: false,
      drawer_changeable: true,
      footer_visible: false,
      footer_title: "",
      footer_row1: "",
      footer_row2: "",
      items: [
        {
          icon: 'view_list',
          title: 'Queue',
          to: '/'
        },
        {
          icon: 'local_movies',
          title: 'Library',
          to: '/library'
        },
        {
          icon: 'settings',
          title: 'Configuration',
          to: '/configuration'
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
        .post("http://" + this.api + "/stop")
        .then(response => {})
        .catch(error => {
          console.log(error)
        })
    }
  },
  created() {
    if (this.$config.dev_endpoint !== "") {
      this.api = this.$config.dev_endpoint
    }

    // Disable drawer.
    if (window.innerWidth >= 1264) {
      this.drawer_changeable = false
      this.drawer = true
    }
    else {
      this.drawer_changeable = true
    }
    window.addEventListener("resize", () => {
      if (window.innerWidth >= 1264) {
        this.drawer_changeable = false
        this.drawer = true
      }
      else {
        this.drawer_changeable = true
      }
    })
    
    // Manage status card.
    let socket = new WebSocket("ws://" + this.api + "/status")
    socket.onopen = (event) => {}
    socket.onmessage = (event) => {
      this.activity = JSON.parse(event.data)
      if (this.activity.status != "free") {
        this.footer_visible = true
        this.footer_title = this.activity.status.charAt(0).toUpperCase() + this.activity.status.slice(1) + "..."
        this.footer_row1 = this.activity.details.name
        this.footer_row2 = 
          "Sequence: " +
          String(Math.floor(this.activity.elasped_secs / 60)) + 
          ":" + 
          (this.activity.elasped_secs - (Math.floor(this.activity.elasped_secs / 60) * 60)).toLocaleString('en-US', {minimumIntegerDigits: 2})
        if (this.activity.status == "playing") {
          this.footer_row2 = 
            "Time: " +
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
        this.footer_title = "Paused"
        this.footer_row1 = ""
        this.footer_row2 = ""
        this.footer_visible = false
      }
    }
  }
}
</script>

<style>
:root {
  background: #000;
}
.expanding-div {
  display: none;
}
@media screen and (max-width: 767px) {
    _::-webkit-full-page-media, _:future, .expanding-div .safari_only {
      display: block !important;
      height: 65px !important;
      max-height: 65px !important;
    }
}
</style>