<template>
  <div>
    <div>
      <b-alert variant="success"
        :show='dismissCountDown'
        dismissible
        fade
        @dismissed="dismissCountDown=0"
      >
      {{ message }}
      </b-alert>
      <br></br>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      dismissSecs: 3,
      dismissCountDown: 0,
      showDismissibleAlert: false,
    };
  },
  props: ['message'],
  /*
    watch: {
          	message: function(newVal, oldVal) { // watch for message changes
              console.log('Prop changed: ', newVal, ' | was: ', oldVal)
              this.dismissCountDown = this.dismissSecs
            }
          },
*/
  methods: {
    showAlert() {
      this.dismissCountDown = this.dismissSecs;
      console.debug('showing message alert');
    },
  },
};
</script>
