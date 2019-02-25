import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import PrimarySearchAppBar from './PrimarySearchAppBar';
import KView from './kview';

function isStockCode(code){
  if(code && code.length===8){
    return code.match(/[sh|sz]\d{6}/i);
  }else{
    return false;
  }
}

class App extends Component {
  constructor(props){
    super(props);
    this.state={code:'SH000001'};
  }
  render() {
    return (
      <div>
        <PrimarySearchAppBar onSearchChange={(text)=>{
            if(isStockCode(text.trim()))this.setState({code:text.trim().toUpperCase()})
          }}/>
        <KView width={'100%'} height={640} code={this.state.code}/>
      </div>
    );
  }
}

export default App;
