import 'bootstrap/dist/css/bootstrap.css';
import Vue from 'vue';
import Router from 'vue-router';
import Samples from './components/Samples.vue';
import Ping from './components/Ping.vue';

Vue.use(Router);

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'Samples',
      component: Samples,
    },
    {
      path: '/ping',
      name: 'Ping',
      component: Ping,
    },
  ],
});
