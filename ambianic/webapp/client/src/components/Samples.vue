<template>
  <div class="container">
    <div class="row">
      <div class="col-sm-10">
        <h1>Samples</h1>
        <hr><br><br>
        <button type="button" class="btn btn-success btn-sm">Add Sample</button>
        <br><br>
        <table class="table table-hover">
          <thead>
            <tr>
              <th scope="col">Title</th>
              <th scope="col">Author</th>
              <th scope="col">Read?</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(sample, index) in samples" :key="index">
              <td>{{ sample.title }}</td>
              <td>{{ sample.author }}</td>
              <td>
                <span v-if="sample.read">Yes</span>
                <span v-else>No</span>
              </td>
              <td>
                <div class="btn-group" role="group">
                  <button type="button" class="btn btn-warning btn-sm">Update</button>
                  <button type="button" class="btn btn-danger btn-sm">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      samples: [],
    };
  },
  methods: {
    getSamples() {
      const path = 'http://localhost:8778/samples';
      axios.get(path)
        .then((res) => {
          this.samples = res.data.samples;
          // console.info('res.data:' + JSON.stringify(res.data));
          // console.info('samples:' + this.samples);
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
  },
  created() {
    this.getSamples();
  },
};
</script>
