import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import PrimarySearchAppBar from './PrimarySearchAppBar';
import KView from './kview';

class App extends Component {
  render() {
    return (
      <div>
        <PrimarySearchAppBar/>
        <KView width={1600} height={1024} />
      </div>
    );
  }
}

export default App;
