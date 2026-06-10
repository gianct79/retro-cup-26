import { mount } from 'svelte';
import App from './App.svelte';
import './styles/index.css';
import './styles/app.css';

mount(App, {
  target: document.getElementById('root'),
});
