import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import PropTypes from 'prop-types';

import { withStyles } from '@material-ui/core/styles';
import CssBaseline from '@material-ui/core/CssBaseline';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import Drawer from '@material-ui/core/Drawer';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import Badge from '@material-ui/core/Badge';
import RadioGroup from '@material-ui/core/RadioGroup';
import Radio from '@material-ui/core/Radio';
import FormControl from '@material-ui/core/FormControl';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import AccountBalance from '@material-ui/icons/AccountBalance';
import ShoppingCart from '@material-ui/icons/ShoppingCart';
import Bookmark from '@material-ui/icons/Bookmark';
import CompanySelect from './CompanySelect';
import Entry from './entry';
import {CompanyContext} from './CompanyContext';
import {clone} from 'lodash';

const drawerWidth = 240;

const styles = theme => ({
  root: {
    display: 'flex',
  },
  appBar: {
    width: `calc(100% - ${drawerWidth}px)`,
    marginLeft: drawerWidth,
  },
  drawer: {
    width: drawerWidth,
    flexShrink: 0,
  },
  drawerPaper: {
    width: drawerWidth,
  },
  toolbar: theme.mixins.toolbar,
  content: {
    flexGrow: 1,
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing.unit * 3,
  },
  grow: {
    flexGrow: 1,
  },
  sectionDesktop: {
    display: 'none',
    [theme.breakpoints.up('md')]: {
      display: 'flex',
    },
  }  
});

class App extends Component {
  constructor(props){
    super(props);
    let idx = 0;
    for(let i=0;i<Entry.length;i++){
      if(Entry[i].default){
        idx = i;
        break;
      }
    }
    this.selector = {
      code:localStorage.code,
      selects:localStorage.selects,
      range:localStorage.range?localStorage.range:"1"
    }
    this.state={
      selectIdx:idx,
      open:false,
      selector:clone(this.selector),
      title:`${localStorage.name} (${localStorage.code})`,
      range:this.selector.range
    };
  }

  handleCloseDialog(result,args){
    if(result==='ok' && args){
      let selects = [];
      let code,name;
      for(let v of args){
        if(v.isSelected)
          selects.push(v);
      }
      if(selects.length>0){
        code = selects[0].code;
        name = selects[0].name;
        this.selector.code = code;
        this.selector.selects = selects;
        this.selector.companys = args;
        this.setState({title:`${name} (${code})`,selector:clone(this.selector)});  
        //将最近的一次选择放入到本地存储中
        localStorage.code = code;
        localStorage.name = name;

        localStorage.selects = selects;
      }
    }
    this.setState({ open:false })
  }

  handeChangeRange(event,value){
    localStorage.range = value;
    this.selector.range = value;
    this.setState({range:value,selector:clone(this.selector)});
  }

  render() {
    const { classes } = this.props;
    const {selector,title,selectIdx,open,range} = this.state;
    //let title = Entry[selectIdx].title;
    let children = Entry[selectIdx].view;

    return (
    <CompanyContext.Provider value={selector}>
    <div className={classes.root}>
      <AppBar position="fixed" className={classes.appBar}>
        <CssBaseline />
        <Toolbar>
          <Typography variant="h6" color="inherit" noWrap>
            {title}
          </Typography>
          <div className={classes.grow} />
          <FormControl component="fieldset">
            <RadioGroup row name="range"  value={range} onChange={this.handeChangeRange.bind(this)}>
                <FormControlLabel value={"1"} control={<Radio />} label="1年" />
                <FormControlLabel value={"5"} control={<Radio />} label="5年" />
                <FormControlLabel value={"10"} control={<Radio />} label="10年" />
                <FormControlLabel value={"20"} control={<Radio />} label="20年" />
                <FormControlLabel value={"40"} control={<Radio />} label="全部" />
            </RadioGroup>                    
          </FormControl>
          <IconButton color="inherit" onClick={()=>this.setState({ open:true })}>
            <Bookmark />
          </IconButton>
          <IconButton color="inherit" onClick={()=>this.setState({ open:true })}>
           <ShoppingCart />
          </IconButton>
          <IconButton color="inherit" onClick={()=>this.setState({ open:true })}>
            <AccountBalance />
          </IconButton>
        </Toolbar>
      </AppBar>        
      <Drawer
          className={classes.drawer}
          variant="persistent"
          anchor="left"
          classes={{
            paper: classes.drawerPaper,
          }}        
          open={true}>
        <List>
          {Entry.map((item, index) => (
            <ListItem button key={item.title}
              selected={index===selectIdx}
              onClick={()=>{this.setState({selectIdx:index})}} >
              <ListItemIcon>{item.icon?item.icon:undefined}</ListItemIcon>
              <ListItemText primary={item.title} />
            </ListItem>
          ))}
        </List>
      </Drawer>
      <main className={classes.content}>
        <div className={classes.toolbar} />
        {children}
      </main>
      <CompanySelect open={open} onClose={this.handleCloseDialog.bind(this)}/>
    </div>
    </CompanyContext.Provider>);
  }
}

export default withStyles(styles, { withTheme: true })(App);
