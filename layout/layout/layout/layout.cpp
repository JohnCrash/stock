// layout.cpp : 此文件包含 "main" 函数。程序执行将在此处开始并结束。
//

#include <Windows.h>

struct MonitorInfo {
	int id;
	HMONITOR hmonitor;
	RECT rc;
};

struct MonitorInfoArray{
	int n;
	MonitorInfo mis[10];

	MonitorInfoArray(){
		n = 0;
	}
};

BOOL MyInfoEnumProc(
	HMONITOR Arg1,
	HDC Arg2,
	LPRECT prc,
	LPARAM Arg4
)
{
	MonitorInfoArray* mia = (MonitorInfoArray* )Arg4;
	int i = mia->n;
	mia->mis[i].id = i;
	mia->mis[i].hmonitor = Arg1;
	mia->mis[i].rc.left = prc->left;
	mia->mis[i].rc.right = prc->right;
	mia->mis[i].rc.top = prc->top;
	mia->mis[i].rc.bottom = prc->bottom;
	mia->n++;
	return TRUE;
}

int SetMonitorPosition(HWND hwnd,int a) {
	MonitorInfoArray mia;
	EnumDisplayMonitors(NULL, NULL, MyInfoEnumProc, (LPARAM)&mia);

	if (a < mia.n && a >= 0) {
		LPRECT prc = &mia.mis[a].rc;
		SetWindowPos(hwnd, HWND_TOP,prc->left,prc->top, prc->right-prc->left,prc->bottom-prc->top, SWP_SHOWWINDOW);
		//ShowWindow(hwnd, SW_MAXIMIZE);
		WINDOWPLACEMENT wpl;
		ZeroMemory(&wpl, sizeof(WINDOWPLACEMENT));
		wpl.length = sizeof(WINDOWPLACEMENT);
		wpl.ptMinPosition.x = prc->left;
		wpl.ptMinPosition.y = prc->top;
		wpl.ptMaxPosition.x = prc->left;
		wpl.ptMaxPosition.y = prc->top;
		wpl.showCmd = SW_SHOWMAXIMIZED;
		wpl.rcNormalPosition = *prc;
		SetWindowPlacement(hwnd, &wpl);
	}
	else {
		MessageBox(NULL, TEXT("不存在指定的显示设备"), TEXT("错误"), MB_OK);
	}
	return 0;
}

//a 将窗口放到第几个显示器上
int launchAndPostion(LPWSTR cmd, LPCWSTR  lpWindowName, LPCWSTR  lpClassName,int a) {
	STARTUPINFO si;
	PROCESS_INFORMATION pi;

	ZeroMemory(&si, sizeof(si));
	si.cb = sizeof(si);
	ZeroMemory(&pi, sizeof(pi));
	HWND hWnd = FindWindow(lpClassName, lpWindowName);
	if (hWnd) {
		SetMonitorPosition(hWnd, a);
	}
	else {
		if (CreateProcess(NULL, cmd, NULL, NULL, FALSE,
			NORMAL_PRIORITY_CLASS | CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP,
			NULL, NULL, &si, &pi)) {
			int count = 0;
			while (1) {
				hWnd = FindWindow(lpClassName, lpWindowName);
				if (hWnd) {
					SetMonitorPosition(hWnd, a);
					break;
				}
				else {
					Sleep(100);
					if (count > 100) { //等待10秒
						MessageBox(NULL, lpWindowName, TEXT("不能定位到窗口"),MB_OK);
						break;
					}
				}
				count++;
			}
			//CloseHandle(pi.hThread);
			//CloseHandle(pi.hProcess);
		}
		else {
			//提示启动失败
			MessageBox(NULL,cmd,TEXT("不能启动程序"), MB_OK);
		}
	}
	return 1;
}

//程序启动平安证券和同花顺远航，并把并把他们放到不同的屏幕上去
int wmain(int argn,LPWSTR argv[])
{
	int nmoniter = _wtoi(argv[4]);
	LPCWSTR pwname = lstrlenW(argv[2]) == 0 ? NULL : argv[2];
	LPCWSTR pwclass = lstrlenW(argv[3])==0?NULL:argv[3];
	launchAndPostion(_wcsdup(argv[1]), pwname,pwclass, nmoniter);

	//launchAndPostion(_wcsdup(TEXT("C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe")), NULL,TEXT("Chrome_WidgetWin_1"), 0);
	//launchAndPostion(_wcsdup(TEXT("F:\\apps\\同花顺远航版\\bin\\happ.exe")),TEXT("同花顺远航版"),NULL,0);
	//launchAndPostion(_wcsdup(TEXT("F:\\pingan\\TdxW.exe")), TEXT("平安证券慧赢V8.16"), TEXT("TdxW_MainFrame_Class"), 1);
}

// 运行程序: Ctrl + F5 或调试 >“开始执行(不调试)”菜单
// 调试程序: F5 或调试 >“开始调试”菜单

// 入门使用技巧: 
//   1. 使用解决方案资源管理器窗口添加/管理文件
//   2. 使用团队资源管理器窗口连接到源代码管理
//   3. 使用输出窗口查看生成输出和其他消息
//   4. 使用错误列表窗口查看错误
//   5. 转到“项目”>“添加新项”以创建新的代码文件，或转到“项目”>“添加现有项”以将现有代码文件添加到项目
//   6. 将来，若要再次打开此项目，请转到“文件”>“打开”>“项目”并选择 .sln 文件
