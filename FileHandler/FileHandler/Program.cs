using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Runtime.InteropServices;
using System.Drawing;


namespace ConsoleApplication1
{
    public struct POINT
    {
        public long x;
        public long y;
    }

    public class WindowFinder
    {
        // For Windows Mobile, replace user32.dll with coredll.dll
        [DllImport("user32.dll", SetLastError = true)]
        public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

        public static IntPtr FindWindow(string caption)
        {
            return FindWindow(String.Empty, caption);
        }

        [DllImport("user32.dll", SetLastError = true)]
        public static extern IntPtr WindowFromPoint(System.Drawing.Point p);


        public static IntPtr WindowFromPoint()
        {
            throw new NotImplementedException();
        }

        [DllImport("user32.dll", ExactSpelling = true, CharSet = CharSet.Auto)]
        public static extern IntPtr GetParent(IntPtr hWnd);


    }

    class Program
    {

        static void Main(string[] args)
        {
            bool found = false;
            Point p1 = new Point();
            p1.X = int.Parse(args[0]);
            p1.Y = int.Parse(args[1]);

            IntPtr MyHwnd = WindowFinder.WindowFromPoint(p1);

            while (WindowFinder.GetParent(MyHwnd) != IntPtr.Zero)
            {
                MyHwnd = WindowFinder.GetParent(MyHwnd);
            }

            var t = Type.GetTypeFromProgID("Shell.Application");
            dynamic o = Activator.CreateInstance(t);
            try
            {
                var ws = o.Windows();
                for (int i = 0; i < ws.Count; i++)
                {
                    var ie = ws.Item(i);
                    if (ie == null || ie.hwnd != (long)MyHwnd)
                        continue;
                  
                    ie.document.folder.MoveHere(args[2]);
                    System.Console.Write("Success");
                    found = true;
                }

                if (!found)
                    System.Console.Write("Desktop");
            }
            finally
            {
                Marshal.FinalReleaseComObject(o);
            }
        }
    }
}
