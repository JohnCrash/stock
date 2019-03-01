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
import AccountBalance from '@material-ui/icons/AccountBalance';
import CompanySelect from './CompanySelect';
import Entry from './entry';

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
    this.state={selectIdx:idx,open:false};
  }

  render() {
    const { classes } = this.props;
    const {selectIdx,open} = this.state;
    let title = Entry[selectIdx].title;
    let children = Entry[selectIdx].view;

    return (<div className={classes.root}>
      <AppBar position="fixed" className={classes.appBar}>
        <CssBaseline />
        <Toolbar>
          <Typography variant="h6" color="inherit" noWrap>
            {title}
          </Typography>
          <div className={classes.grow} />
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
      <CompanySelect open={open} onClose={()=>this.setState({ open:false })}/>
    </div>);
  }
}

export default withStyles(styles, { withTheme: true })(App);
