<template>
  <div class="container">
    <div class="row">
      <div class="col-sm-10">
        <h1>Samples</h1>
        <hr><br><br>
        <alert ref='alert' :message="message"></alert>
        <button
          type="button"
          class="btn btn-success btn-sm"
          v-b-modal.sample-modal
        >
          Add Sample
        </button>
        <br><br>
        <table class="table table-hover">
          <thead>
            <tr>
              <th scope="col">File</th>
              <th scope="col">ID</th>
              <th scope="col">Datetime</th>
              <th scope="col">Image</th>
              <th scope="col">Inference Results</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(sample, index) in samples" :key="index">
              <td>{{ sample.file }}</td>
              <td>{{ sample.id }}</td>
              <td>{{ sample.datetime }}</td>
              <td>{{ sample.image }}</td>
              <td>
                <ul v-for="inf in sample.inference_result" :key="index">
                  <li>
                    <p>Category: {{inf.category}}</p>
                    <p>Confidence: {{inf.confidence}}</p>
                    <p>Box: {{inf.box}}</p>
                  </li>
                </ul>
              </td>
<!--
              <td>
                <span v-if="sample.read">Yes</span>
                <span v-else>No</span>
              </td>
-->
              <td>
                <div class="btn-group" role="group">
                  <button
                          type="button"
                          class="btn btn-warning btn-sm"
                          v-b-modal.sample-update-modal
                          @click="editSample(sample)">
                      Update
                  </button>
                  <button
                    type="button"
                    class="btn btn-danger btn-sm"
                    @click="onDeleteSample(sample)"
                  >
                  Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <b-modal ref="addSampleModal"
             id="sample-modal"
             title="Add a new sample"
             hide-footer>
      <b-form @submit="onSubmit" @reset="onReset" class="w-100">
      <b-form-group id="form-title-group"
                    label="Title:"
                    label-for="form-title-input">
          <b-form-input id="form-title-input"
                        type="text"
                        v-model="addSampleForm.title"
                        required
                        placeholder="Enter title">
          </b-form-input>
        </b-form-group>
        <b-form-group id="form-author-group"
                      label="Author:"
                      label-for="form-author-input">
            <b-form-input id="form-author-input"
                          type="text"
                          v-model="addSampleForm.author"
                          required
                          placeholder="Enter author">
            </b-form-input>
          </b-form-group>
        <b-form-group id="form-read-group">
          <b-form-checkbox-group v-model="addSampleForm.read" id="form-checks">
            <b-form-checkbox value="true">Read?</b-form-checkbox>
          </b-form-checkbox-group>
        </b-form-group>
        <b-button type="submit" variant="primary">Submit</b-button>
        <b-button type="reset" variant="danger">Reset</b-button>
      </b-form>
    </b-modal>
    <b-modal ref="editSampleModal"
             id="sample-update-modal"
             title="Update"
             hide-footer>
      <b-form @submit="onSubmitUpdate" @reset="onResetUpdate" class="w-100">
      <b-form-group id="form-title-edit-group"
                    label="Title:"
                    label-for="form-title-edit-input">
          <b-form-input id="form-title-edit-input"
                        type="text"
                        v-model="editSampleForm.title"
                        required
                        placeholder="Enter title">
          </b-form-input>
        </b-form-group>
        <b-form-group id="form-author-edit-group"
                      label="Author:"
                      label-for="form-author-edit-input">
            <b-form-input id="form-author-edit-input"
                          type="text"
                          v-model="editSampleForm.author"
                          required
                          placeholder="Enter author">
            </b-form-input>
          </b-form-group>
        <b-form-group id="form-read-edit-group">
          <b-form-checkbox-group v-model="editSampleForm.read" id="form-checks">
            <b-form-checkbox value="true">Read?</b-form-checkbox>
          </b-form-checkbox-group>
        </b-form-group>
        <b-button-group>
          <b-button type="submit" variant="primary">Update</b-button>
          <b-button type="reset" variant="danger">Cancel</b-button>
        </b-button-group>
      </b-form>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios';
import Alert from './Alert.vue';
import ambianic_conf from '../config.js'

const API_SAMPLES_PATH = ambianic_conf['AMBIANIC_API_URI'] + 'samples';
console.debug("API_SAMPLES_PATH: "+API_SAMPLES_PATH)

export default {
  data() {
    return {
      samples: [],
      addSampleForm: {
        title: '',
        author: '',
        read: false,
      },
      editSampleForm: {
        id: '',
        title: '',
        author: '',
        read: false,
      },
      message: '',
      showMessage: false,
    };
  },
  components: {
    alert: Alert,
  },
  methods: {
    getSamples() {
      const path = API_SAMPLES_PATH
      axios.get(path)
        .then((res) => {
          this.samples = res.data.samples;
          //console.debug('res.data:' + JSON.stringify(res.data));
          //console.debug('samples:' + JSON.stringify(this.samples));
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    addSample(payload) {
      const path = API_SAMPLES_PATH;
      axios.post(path, payload)
        .then(() => {
          this.getSamples();
          this.message = 'Sample added!';
          this.$refs.alert.showAlert()
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getSamples();
        });
    },
    updateSample(payload, sampleID) {
      //console.debug('updating sample id: ' + sampleID + ' paylod: ' + JSON.stringify(payload));
      const path = API_SAMPLES_PATH + `/${sampleID}`;
      axios.put(path, payload)
        .then(() => {
          this.getSamples();
          this.message = 'Sample updated!';
          this.$refs.alert.showAlert()
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getSamples();
        });
    },
    initForm() {
      this.addSampleForm.title = '';
      this.addSampleForm.author = '';
      this.addSampleForm.read = false;
      this.editSampleForm.id = '';
      this.editSampleForm.title = '';
      this.editSampleForm.author = '';
      this.editSampleForm.read = false;
    },
    onSubmit(evt) {
      evt.preventDefault();
      this.$refs.addSampleModal.hide();
      let read = false;
      if (this.addSampleForm.read) read = true;
      const payload = {
        title: this.addSampleForm.title,
        author: this.addSampleForm.author,
        read, // property shorthand
      };
      this.addSample(payload);
      this.initForm();
    },
    onReset(evt) {
      evt.preventDefault();
      this.$refs.addSampleModal.hide();
      this.initForm();
    },
    editSample(sample) {
      // console.info('Transfering sample from table to edit form: ' + JSON.stringify(sample));
      this.editSampleForm = sample;
    },
    onSubmitUpdate(evt) {
      evt.preventDefault();
      this.$refs.editSampleModal.hide();
      let read = false;
      if (this.editSampleForm.read) read = true;
      const payload = {
        title: this.editSampleForm.title,
        author: this.editSampleForm.author,
        read,
      };
      this.updateSample(payload, this.editSampleForm.id);
    },
    onResetUpdate(evt) {
      evt.preventDefault();
      this.$refs.editSampleModal.hide();
      this.initForm();
      this.getSamples(); // update view
    },
    deleteSample(sampleID) {
      const path = API_SAMPLES_PATH + `/${sampleID}`;
      axios.delete(path)
        .then(() => {
          this.getSamples();
          this.message = 'Sample removed!';
          this.$refs.alert.showAlert()
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getSamples();
        });
    },
    onDeleteSample(sample) {
      this.deleteSample(sample.id);
    },
  },
  created() {
    this.getSamples();
  },
};
</script>
