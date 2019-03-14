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
import RadioGroup from '@material-ui/core/RadioGroup';
import Radio from '@material-ui/core/Radio';
import FormControl from '@material-ui/core/FormControl';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import AccountBalanceIcon from '@material-ui/icons/AccountBalance';
import ShoppingCartIcon from '@material-ui/icons/ShoppingCart';
import NavigateBeforeIcon from '@material-ui/icons/NavigateBefore';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import CheckIcon from '@material-ui/icons/Check';
import Badge from '@material-ui/core/Badge';
import ExposurePlus1Icon from '@material-ui/icons/ExposurePlus1';
import ExposureZeroIcon from '@material-ui/icons/ExposureZero';
import ExposureNeg1Icon from '@material-ui/icons/ExposureNeg1';
import ExposureNeg2Icon from '@material-ui/icons/ExposureNeg2';
import BookmarkIcon from '@material-ui/icons/Bookmark';
import AddShoppingCartIcon from '@material-ui/icons/AddShoppingCart';
import SearchIcon from '@material-ui/icons/Search';
import {postJson} from './fetch';
import CompanySelect from './CompanySelect';
import Entry from './entry';
import {CompanyContext} from './CompanyContext';
import {clone} from 'lodash';
import CompanyInfo from './CompanyInfo';
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';
import Link from '@material-ui/core/Link';

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
  },
  primary: {},
  icon: {},
  link: {
    margin: theme.spacing.unit,
  }  
});

const searchIndex = 6;
let menus = [
  {label:'买入的股票',icon:<ShoppingCartIcon/>,key:'cart',tables:[]},
  {label:'收藏夹',icon:<BookmarkIcon/>,key:'bookmark',tables:[]},
  {label:'即将为正',icon:<ExposurePlus1Icon/>,key:'ready',tables:[]},
  {label:'当前为正',icon:<ExposureZeroIcon/>,key:'today',tables:[]},
  {label:'昨天为正',icon:<ExposureNeg1Icon/>,key:'yesterday',tables:[]},
  {label:'三天前为正',icon:<ExposureNeg2Icon/>,key:'threeday',tables:[]},
  {label:'条件筛选',icon:<SearchIcon/>,key:'search',tables:[]}
];

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
      range:this.selector.range,
      anchorEl:null,
      menuSel:0,
      currentNum:0,
      currentSel:0
    };
  }
  componentDidMount(){
    this.requstSelectList();
  }
  errorMessage(str){
    console.error(str);
  }
  /**
   * 将股票列表加载进来
   */
  requstSelectList(){
    //FIXBUG postJson在componentDidMount可能不响应
    //放在setTimeout中正常相应？
    setTimeout(()=>postJson('/api/selects',{},(json)=>{
      if(json && json.results){
        for(let it of menus){
          it.tables = [];
          for(let com of json.results){
            com.id = com.company_id;
            if(com[it.key]===1)
              it.tables.push(com);
          }
        }
        this.setState({currentNum:menus[this.state.menuSel].tables.length,currentSel:1});
        this.selectCompanyByIndex(this.state.menuSel,1);
      }else{
        this.errorMessage('not found new stock');
      }
    }),0);
  }
  handleCloseDialog(result,args){
    let menu = menus[this.state.menuSel];
    let idx = 0;
    if(result==='ok' && args){
      let selects = [];
      let code,name;

      if(this.state.menuSel===searchIndex){
        args.sort((a,b)=>b.income-a.income);
        menus[searchIndex].tables = args;
        for(let v of args){
          if(v.isSelected)
            selects.push(v);
        }  
      }else{
        menu.tables.sort((a,b)=>b.income-a.income);
        for(let i in menu.tables){
          let v = menu.tables[i];
          if(v.isSelected){
            idx = Number(i);
            selects.push(v);
          }
        }  
      }

      if(selects.length>0){
        code = selects[0].code;
        name = selects[0].name;
      }else if(menu.tables.length>0){
        code = menu.tables[0].code;
        name = menu.tables[0].name;
      }
      this.selector.code = code;
      this.selector.selects = selects;
      this.selector.companys = args;
      this.setState({title:`${name} (${code})`,selector:clone(this.selector)});  
      //将最近的一次选择放入到本地存储中
      localStorage.code = code;
      localStorage.name = name;

      localStorage.selects = selects;
    }
    let count =menus[this.state.menuSel].tables.length;
    this.setState({ open:false,anchorEl:null,currentNum:count,currentSel:count>0?idx+1:0 });
    this.selectCompanyByIndex(this.state.menuSel,idx+1)
  }
  selectCompanyByIndex(menuSel,i){
    let t = menus[menuSel].tables;
    if(t && i-1>=0 && i-1<t.length){
      let com = menus[menuSel].tables[i-1];
      let code = com.code;
      let name = com.name;
      this.selector.code = code;
      this.setState({title:`${name} (${code})`,selector:clone(this.selector)});  
      localStorage.code = code;
      localStorage.name = name;
    }
  }
  handeChangeRange(event,value){
    localStorage.range = value;
    this.selector.range = value;
    this.setState({range:value,selector:clone(this.selector)});
  }
  handleClose = ()=>{
    this.setState({ anchorEl: null });
  }
  handleMenuSelect = (i)=>()=>{
    let count = menus[i].tables.length;
    if(menus[i].key==='search'){
      this.setState({ open:true,menuSel:i,anchorEl:null,currentNum:0,currentSel:0 });
    }else{
      this.setState({open:true,menuSel:i,anchorEl:null,currentNum:count,currentSel:count>0?1:0});
    }
    this.selectCompanyByIndex(i,1);
  }
  handlePrev = ()=>{
    const {menuSel,currentNum,currentSel} = this.state;
    if(currentNum>0){
      let sel = currentSel-1<1?1:currentSel-1
      this.setState({currentSel:sel});
      this.selectCompanyByIndex(menuSel,sel);
    }else{
      this.setState({currentSel:0});
    }
  }
  handleNext = ()=>{
    const {menuSel,currentNum,currentSel} = this.state;
    if(currentNum>0){
      let sel = currentSel>=currentNum?currentNum:currentSel+1;
      this.setState({currentSel:sel});
      this.selectCompanyByIndex(menuSel,sel);
    }else{
      this.setState({currentSel:0});
    }
  }
  handleAddShopping = ()=>{

  }
  handleBookmark = ()=>{
    
  }
  render() {
    const { classes } = this.props;
    const {selector,title,selectIdx,open,range,anchorEl,menuSel,currentNum,currentSel} = this.state;
    let children = Entry[selectIdx].view;
    let currentMenu = menus[menuSel];
    return (
    <CompanyContext.Provider value={selector}>
    <div className={classes.root}>
      <AppBar position="fixed" className={classes.appBar}>
        <CssBaseline />
        <Toolbar>
          <Typography variant="h6" color="inherit" noWrap>
            <Link variant="h6" component="button" className={classes.link} color={'inherit'}
              onClick={()=>{window.open(`https://xueqiu.com/S/${this.selector.code}`)}}>
              {title}
            </Link>
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
          <IconButton color="inherit" onClick={this.handleAddShopping}>
            <AddShoppingCartIcon/>
          </IconButton>
          <IconButton color="inherit" onClick={this.handleBookmark}>
            <BookmarkIcon/>
          </IconButton>
          <IconButton color="inherit" onClick={this.handlePrev}>
            <Badge className={classes.margin} badgeContent={currentSel} color="secondary">
              <NavigateBeforeIcon />
            </Badge>
          </IconButton>
          <IconButton color="inherit" onClick={(event)=>this.setState({ anchorEl: event.currentTarget })}>
            <Badge className={classes.margin} badgeContent={currentNum} color="secondary">
              {menus[menuSel].icon}
            </Badge>
          </IconButton>
          <IconButton color="inherit" onClick={this.handleNext}>
            <Badge className={classes.margin} badgeContent={currentNum-currentSel} color="secondary">
              <NavigateNextIcon />
            </Badge>
          </IconButton>          
          <Menu
            id="simple-menu"
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={this.handleClose}
          >
            {menus.map((item,i)=>{
              return <MenuItem selected={menuSel===i} key={item.key} onClick={this.handleMenuSelect(i)}>
                  <Badge className={classes.margin} badgeContent={item.tables?item.tables.length:0} color="secondary">
                  <ListItemIcon className={classes.icon}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText classes={{ primary: classes.primary }} inset primary={item.label} />
                  </Badge>
                </MenuItem>  
            })}
          </Menu>          
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
        <CompanyInfo />
      </Drawer>
      <main className={classes.content}>
        <div className={classes.toolbar} />
        {children}
      </main>
      <CompanySelect open={open} title={currentMenu.label} search={currentMenu.key==='search'} lists={currentMenu.key==='search'?undefined:currentMenu.tables} onClose={this.handleCloseDialog.bind(this)}/>
    </div>
    </CompanyContext.Provider>);
  }
}

export default withStyles(styles, { withTheme: true })(App);
