"""
基于beeware编写的一款Todo程序.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import pickle
from datetime import date,timedelta


'''数据结构模块.'''
#目标
class Goal:
    """目标类."""
    def __init__(self, name, subgroup=None):
        self.name = name
        self.subgroup = subgroup if not subgroup is None else list()

    def add(self, group):
        self.subgroup.append(group)

    def __repr__(self):
        return f"Goal({self.name})"

    def build_page(self):
        """构建Goal的盒子."""
        box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        for group in self.subgroup:
            box.add(group.build_page(), toga.Divider())
        return box

#任务组
class Group:
    """任务组类."""
    def __init__(self, name:str, parent_goal:Goal, subtask=None):
        self.name = name
        self.subtask= subtask if not subtask is None else list()
        self.parent_goal = parent_goal
        self.parent_goal.add(self)

    def add(self, task):
        self.subtask.append(task)

    def __repr__(self):
        return f"Group({self.name})"

    def build_page(self):
        box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        box.add(
            toga.Label(
                text=f"任务组：{self.name}"
            )
        )

        for task in self.subtask:
            subbox = toga.Box(
                children=[
                    toga.Box(style=Pack(flex=1)),#占位盒子，产生缩进
                    toga.Label(text=f"{task.name}", style=Pack(flex=10))#显示任务的名字
                ]
            )
            box.add(subbox)


        return box
#任务
class Task:
    """任务类"""
    def __init__(self, name, start_date, end_date, date_step, importance, excp_times, tags, parent_group, description):
        """向父组添加自己."""
        self.name=name
        self.start_date=start_date
        self.end_date=end_date
        self.date_step=date_step
        self.importance=importance
        self.excp_times=excp_times
        self.tags=tags
        self.parent_group=parent_group
        self.description=description
        self.finished_times= 0
        self.is_finished=False

        self.parent_group.add(self)
    
    def finish(self):
        """任务按钮被点击时, 做出的所有反应"""
        self.finished_times += 1
        if self.finished_times == self.excp_times:
            self.is_finished = True
          
    def __iter__(self):
            yield 'name', self.name
            yield 'start_date', self.start_date
            yield 'end_date', self.end_date
            yield 'date_step', self.date_step
            yield 'importance', self.importance
            yield 'excp_times', self.excp_times
            yield 'tags', self.tags
            yield 'parent_group', self.parent_group
            yield 'description', self.description
            yield 'finished_times', self.finished_times
            yield 'is_finished', self.is_finished


    def __str__(self):
        return self.name \
        + f"[{self.finished_times}次/{self.excp_times}次]" \
        + "\n" \
        + "".join([" #"+tag for tag in self.tags])

    def __repr__(self):
        return f"Task({self.name})"
      
#数据类
class Data:
    """
    储存全体数据的类.
    """
    def __init__(self):
        self.default_goal = Goal(name="日常")
        self.default_group = Group(name="默认组", parent_goal=self.default_goal)
        self.all_goals = [self.default_goal] 
        self.all_groups = [self.default_group]
        self.today_task = [Task(**{
            "name":"第一个任务",
            "start_date":tuple(Date.today()),
            "end_date":tuple(Date.today()),
            "date_step":1,
            "importance":0,
            "excp_times":1,
            "tags":("第一次", "教程"),
            "parent_group":self.default_group,
            "description":"一个测试任务.",
            })]
        self.past_task = []
        self.today_finish = []
        self.active_task = self.today_task.copy()

        self.is_first_time_opened = True #是否初次打开
        self.first_time_opened = tuple(Date.today()) #初次打开的日期
    
    def update(self):
        """
        处理Data里面的数据, 更新状态.
        """
        self.today_task.clear()
        for task in self.active_task:
            #今天的任务
            if date(*task.start_date) <= date.today() <= date(*task.end_date):
                #加入今天的任务
                self.today_task.append(task)

                #完成的任务处理（今天）
                if task.is_finished and task not in self.past_task:
                    self.past_task.append(task)
                    self.today_finish.append(task)

            #过去的任务
            elif date(*task.end_date) <= date.today():
                #完成的任务处理（非今天）
                if task.is_finished and task not in self.past_task:
                    self.active_task.remove(task)
                    self.past_task.append(task)

            #将来的任务
            else:
                pass
            



class Date(date):
    def __iter__(self):
        return iter((self.year, self.month, self.day))

############################################
'''定制界面模块.'''

class Task_interface(toga.Box):
    '''任务界面定制类'''
    def __init__(self, data, **args):
        super().__init__(**args)
        #界面定制
        self.style.direction = COLUMN #强制为竖排
        self.style.flex = 1
        self.name = "任务"
        self.data = data #获取数据库
        self.update()

    def new_on_press(self, widget):
        """New按钮点击时的响应函数."""
        new_task_interface = Detail_interface(self.data)
        self.app.switch_to(new_task_interface)


    def update(self):
        """刷新自身界面."""


        self.clear()
        self.box = toga.Box(
                style=Pack(direction=COLUMN, flex=1)
            )

        #新建按钮
        new_button = toga.Button(
            "New", 
            style=Pack(direction=ROW, flex=1),
            on_press=self.new_on_press  #New按钮被点击的反应
        )
        self.box.add(new_button)

        def task_on_press(task):
            def func(widget):
                """点击的反应:修改label,取消button, 弹出弹窗, 修改task"""
                task.finish()
                self.data.update()
                if task.is_finished:
                    task.label.text = "(已完成)" + task.label.text
                    task.button.enabled = False
                    task.button.text = "☑"
                    self.window.info_dialog(title="任务完成", message=f'任务"{task.name}"已完成！')
                self.update()
            return func

        #任务列表
        for task in DATA.today_task:
            task.button = toga.Button(
                text="〇" if not task.is_finished else "☑",
                on_press = task_on_press(task),
                enabled = True if not task.is_finished else False)

            task.label = toga.Label(
                text=str(task) if not task.is_finished else "(已完成)"+str(task)
            )

            self.box.add(
                toga.Box(
                    children=[task.button, task.label], 
                    style=Pack(direction=ROW))
            ) #单个任务条的样式
            

        #滑动条
        self.add(toga.ScrollContainer(
            style=Pack(flex=1), 
            horizontal=True, 
            vertical=True, 
            content=self.box
        ))


class Schedule_interface(toga.Box):
    """日程界面定制类"""
    def __init__(self, data, **args):
        super().__init__(**args)
        self.style.direction = COLUMN #强制为竖排
        self.style.flex = 1
        self.name = "日程" 
        self.data = data

        self.update()
    def update(self):
        self.clear()



        self.box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        schedule = {i:list() for i in range(7)}
        for task in self.data.active_task:

            #添加任务
            if (date.today()-date(*task.start_date)).days >=0: #如果任务已经开始

                for i in range(
                    max((date(*task.start_date)-date.today()).days, 0), 
                    min((date(*task.end_date)-date.today()).days+1 ,7), 
                    task.date_step):

                    schedule[i].append(task)

        for i in schedule:
            if len(schedule[i])>0:
                this_day = (date.today()+timedelta(days=i)).strftime("%y年%m月%d日")

                day_bar = toga.Label(
                    text=f"接下来的第{i}天({this_day}):",
                    style=Pack(direction=ROW,flex=1)
                    )
                
                task_list = toga.Box(
                    children=[toga.Box(
                        children=[
                            toga.Label("任务名:"+task.name+f"[{task.parent_group.parent_goal.name}]({task.parent_group.name}), 已完成{task.finished_times}次/{task.excp_times}次"),
                            toga.Label("    ->任务描述:"+(task.description if len(task.description) <20 else "\t"+task.description[:20]+"...") ),
                            toga.Label("----------")
                        ],
                        style=Pack(direction=COLUMN,flex=1)
                    )    
                         for task in schedule[i]
                    ],
                    style=Pack(direction=COLUMN,flex=1)
                )

                self.box.add(day_bar, task_list ,toga.Divider())

        self.add(toga.ScrollContainer(
            style=Pack(flex=1), 
            horizontal=True, 
            vertical=True, 
            content=self.box
        ))


class Goal_interface(toga.Box):
    '''目标界面定制类'''
    def __init__(self, data, **args):
        super().__init__(**args)
        self.style.direction = COLUMN #强制为竖排
        self.style.flex = 1
        self.name = "目标"
        self.data = data

        self.update()
    def update(self):
        self.clear()
        self.box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        # 加载布局
        self.nevigating_box=toga.Box(style=Pack(direction=ROW))
        self.task_box=toga.Box(style=Pack(direction=COLUMN, flex=1))

        #向目标栏加入新建目标按钮
        def new_goal(widget):
            self.box.clear()
            self.box.add(New_goal_interface(self.data))
        
        self.nevigating_box.add(
            toga.Button(
                text="新建目标",
                on_press=new_goal
            )
        )

        # 对于每一个目标, 指定一个显示子组的函数
        def goal_on_press(goal):
            def func(widget):
                self.task_box.clear()
                self.task_box.add(goal.build_page())
                self.goal = goal
            ## 切换函数
            return func

        # 添加目标导航栏的按钮
        for goal in self.data.all_goals:
            self.nevigating_box.add(
                toga.Button(
                    text=goal.name,
                    on_press=goal_on_press(goal)
                )
            )
        
        #新建子组的按钮
        def new_group(widget):
            self.box.clear()
            self.box.add(New_group_interface(data=self.data, parent_goal=self.goal))

        self.new_group_button = toga.Button(
            text="新建子组",
            on_press=new_group,
            style=Pack(flex=1)
        )
        

        # 加载默认的布局
        self.goal = self.data.all_goals[0]
        self.task_box.add(self.data.all_goals[0].build_page())
        self.box.add(
            self.nevigating_box, 
            self.new_group_button, 
            self.task_box
            )
            


        # 加载滑动条
        self.add(toga.ScrollContainer(
            style=Pack(flex=1), 
            horizontal=True, 
            vertical=True, 
            content=self.box
        ))


class Statics_interface(toga.Box):
    """统计界面定制类"""
    def __init__(self, data, **args):
        super().__init__(**args)
        self.style.direction = COLUMN #强制为竖排
        self.style.flex = 1
        self.name = "统计"
        self.data = data

        self.add(toga.Label("Ciallo", style=Pack(alignment="center")))

        self.update()
    def update(self):
        self.clear()
        self.box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        labels = {}
        labels['打招呼'] = toga.Label(text='Ciallo! 欢迎使用ToyPlan~')
        labels['第一次打开的时间'] = toga.Label(text='第一次打开的时间:{}年{}月{}日'.format(*self.data.first_time_opened))
        labels['总目标数'] = toga.Label(text=f'总目标数:{len(self.data.all_goals)}')
        labels['总任务数'] = toga.Label(text=f'总任务数:{len(self.data.active_task)+len(self.data.past_task)-len(self.data.today_finish)}')
        labels['今天完成的任务'] = toga.Label(text=f'今天完成的任务:{len(self.data.today_finish)}')
        labels['所有已经完成的任务'] = toga.Label(text=f'所有已经完成的任务:{len(self.data.past_task)}')
        

        self.box.add(*labels.values())

        self.add(toga.ScrollContainer(
            style=Pack(flex=1), 
            horizontal=True, 
            vertical=True, 
            content=self.box
        ))


class Nevigation_bar(toga.Box): 
    """导航栏定制类"""
    def __init__(self, main_box, interfaces, **args):
        """定制一个导航栏.
        其中参数main_box是进行切换的容器, interfaces是可以进行切换的页面.
        """
        super().__init__(**args)
        #强制为横排
        self.style.direction = ROW

        self.main_box = main_box

        def on_press_func(box):
            def func(widget):
                """切换按钮响应函数."""
                self.main_box.clear()
                box.update()
                self.main_box.add(box, self)
                self.main_box.refresh()
            return func
        
        for box in interfaces:
            #添加切换按钮
            self.add(
                toga.Button(
                    box.name,
                    on_press = on_press_func(box),
                    style=Pack(flex=1)
                )
            )


class Detail_interface(toga.Box):
    """任务详情与填写页面定制类"""
    def __init__(self, data, **args):
        super().__init__(**args)
        #界面初始化
        self.style.direction = COLUMN
        self.style.flex=1

        #传入数据库, 为添加任务做准备
        self.data = data

        self.detail_box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        self.name_label = toga.Label(text="任务名称")
        self.name_bar = toga.TextInput()
        self.start_date_label = toga.Label(text="开始日期:")
        self.start_date_bar = toga.DateInput()
        self.end_date_label = toga.Label(text="结束日期:")
        self.end_date_bar = toga.DateInput()
        self.date_step_label = toga.Label(text="日期步频:")
        self.date_step_bar = toga.NumberInput(step=1, min=1, value=1)
        self.importance_label = toga.Label(text="重要性指标(输入零到一百的数字):")
        self.importance_bar = toga.NumberInput(step=1, min=0, max=100, value=0)
        self.excp_times_label = toga.Label(text="需要完成的次数:")
        self.excp_times_bar = toga.NumberInput(step=1, min=1, value=1)
        self.tags_label = toga.Label(text="Tags(用空格分开):")
        self.tags_bar = toga.TextInput()
        self.parent_group_label = toga.Label(text="任务组")
        self.parent_group_bar = toga.Selection(
            items=[
                f"({group.parent_goal.name}):{group.name}" for group in DATA.all_groups
                ]
            )
        self.description_label = toga.Label(text="任务描述")
        self.description_bar = toga.MultilineTextInput()


        self.detail_box.add(
            self.name_label,self.name_bar,
            self.excp_times_label,self.excp_times_bar,
            self.start_date_label,self.start_date_bar,
            self.end_date_label,self.end_date_bar,
            self.date_step_label,self.date_step_bar, 
            self.importance_label, self.importance_bar,
            self.parent_group_label,self.parent_group_bar,
            self.tags_label,self.tags_bar,
            self.description_label,self.description_bar
        )

        #加入滑动条
        self.add(
            toga.ScrollContainer(
                content=self.detail_box, 
                style=Pack(direction=COLUMN,flex=10)
                )
        )

        #加入确认与取消按钮
        self.comfirm_button = toga.Button(text="确认", 
        on_press=self.comfirm, 
        style=Pack(direction=ROW, flex=1)
        )

        self.cancel_button = toga.Button(text="取消", 
        on_press=self.cancel, 
        style=Pack(direction=ROW, flex=1)
        )

        self.add(toga.Box(
            children=[self.cancel_button, self.comfirm_button],
            style=Pack(direction=ROW)
        ))

    def comfirm(self, widget):
        """任务界面确定按钮响应函数"""
        if len(self.name_bar.value)==0:
            self.window.info_dialog(title="空的任务名", message="您似乎没有输入任务名称捏~")
        #找到对应组
        group_dic = {f"({group.parent_goal.name}):{group.name}":group for group in DATA.all_groups}
        #新建任务
        task = Task(
            name = self.name_bar.value, 
            start_date = self.start_date_bar.value.timetuple()[0:3], 
            end_date=self.end_date_bar.value.timetuple()[0:3], 
            date_step=int(self.date_step_bar.value), 
            importance=int(self.importance_bar.value), 
            excp_times=int(self.excp_times_bar.value), 
            tags=self.tags_bar.value.split(), 
            parent_group=group_dic[self.parent_group_bar.value], 
            description=self.description_bar.value
        )
        #添加任务到数据库
        self.data.active_task.append(task)
        #更新数据库
        self.data.update()
        

        #刷新显示
        self.app.task_interface.update()


        #回到任务窗口
        self.app.switch_to(self.app.task_interface, self.app.nevigation_bar)


    def cancel(self, widget):
        """任务界面取消按钮响应函数"""
        #回到任务窗口
        self.app.switch_to(self.app.task_interface, self.app.nevigation_bar)


class New_goal_interface(toga.Box):
    """新建目标界面定制类"""
    def __init__(self, data, **args):
        super().__init__(**args)
        self.style.direction = COLUMN #强制为竖排
        self.style.flex = 1
        self.data = data

        self.box = toga.Box(style=Pack(direction=ROW, flex=1))

        self.label = toga.Label("新的目标名：")
        self.input_box = toga.TextInput(style=Pack(flex=1), on_confirm=self.confirm)
        self.box.add(self.label, self.input_box)

        self.comfirm_button = toga.Button(text="确定",on_press=self.confirm,style=Pack(flex=1))
        self.cancel_button = toga.Button(text="取消",on_press=self.cancel,style=Pack(flex=1))

        self.add(self.box, self.comfirm_button, self.cancel_button)


    def confirm(self, widget):
        """任务界面取消按钮响应函数"""
        if len(self.input_box.value)==0:
            self.window.info_dialog(title="空的目标名", message="您似乎没有输入目标名称捏~")
        new_goal = Goal(name=self.input_box.value)
        self.data.all_goals.append(new_goal)
        self.data.update()
        #回到任务窗口
        self.app.goal_interface.update()
    def cancel(self, widget):
        """任务界面取消按钮响应函数"""
        #回到任务窗口
        self.app.goal_interface.update()


class New_group_interface(toga.Box):
    """新建组界面定制类"""
    def __init__(self, data, parent_goal, **args):
        super().__init__(**args)
        self.style.direction = COLUMN #强制为竖排
        self.style.flex = 1
        self.data = data
        self.parent_goal = parent_goal

        self.box = toga.Box(style=Pack(direction=ROW, flex=1))

        self.label = toga.Label(f"在目标[{self.parent_goal.name}]下新建任务组.\n新的任务组名：")
        self.input_box = toga.TextInput(style=Pack(flex=1), on_confirm=self.confirm)
        self.box.add(self.label, self.input_box)

        self.comfirm_button = toga.Button(text="确定",on_press=self.confirm,style=Pack(flex=1))
        self.cancel_button = toga.Button(text="取消",on_press=self.cancel,style=Pack(flex=1))

        self.add(self.box, self.comfirm_button, self.cancel_button)


    def confirm(self, widget):
        """界面取消按钮响应函数"""
        if len(self.input_box.value)==0:
            self.window.info_dialog(title="空的任务组名", message="您似乎没有输入任务组名称捏~")
        new_group = Group(name=self.input_box.value, parent_goal=self.parent_goal)
        self.data.all_groups.append(new_group)
        self.data.update()
        #回到窗口
        self.app.goal_interface.update()
    def cancel(self, widget):
        """界面取消按钮响应函数"""
        #回到窗口
        self.app.goal_interface.update()


#############################################################
#数据载入模块, 本地读取已有任务

DATA = Data()

############################################################
class ToyList(toga.App):
    def startup(self):

        #主窗口
        self.main_box = toga.Box(style=Pack(direction=COLUMN))

        #各个主界面的盒子
        #任务界面
        self.task_interface = Task_interface(DATA, id="task_interface") 
        #日程界面
        self.schedule_interface = Schedule_interface(DATA,id="schedule_interface")
        #目标界面
        self.goal_interface = Goal_interface(DATA,id="goal_interface")
        #统计界面
        self.statics_interface = Statics_interface(DATA,id="statics_interface")
        #导航栏
        self.nevigation_bar = Nevigation_bar(
            main_box = self.main_box,
            interfaces = [
                self.task_interface,
                self.schedule_interface,
                self.goal_interface,
                self.statics_interface,
            ],
            id="nevigation_bar"
        )

        #主窗口显示任务界面与导航栏
        self.main_box.add(self.task_interface, self.nevigation_bar)


        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        size = 360 
        self.main_window.size = (size, 1.618*size)
        self.main_window.show()

    def switch_to(self, *interface):
        """"""
        self.main_box.clear()
        self.main_box.add(
            *interface
        )


def main():
    return ToyList()

