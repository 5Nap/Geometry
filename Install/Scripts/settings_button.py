# coding: utf-8

import sys
import Tkinter as tk


N, S, E, W = tk.N, tk.S, tk.E, tk.W


class GUI(tk.Frame):

	def __init__(self, master=None, els=[]):
		tk.Frame.__init__(self, master)
		self.grid(sticky=N+S+E+W)
		tk.Grid.rowconfigure(self, 0, weight=1)
		tk.Grid.columnconfigure(self, 0, weight=1)

		self.elementList = els[:-2]
		self.elDict = {}
		self.outDict = {els[k][0]:els[k][1] for k in range(len(els))}
		self.alignRoads = tk.IntVar()
		self.readField = tk.IntVar()

		self.__createWidgets()

	def __createWidgets(self):
		top = self.winfo_toplevel()
		self.top = top

		self.rowconfigure(1, weight=1)
		self.columnconfigure(0, weight=1)

		self.f1 = tk.Frame(self, height=120, width=120, bg='#eeeeee')
		self.f1.grid(row=0, sticky=N+E+W+S, columnspan=2)
		tk.Grid.rowconfigure(self.f1, 0, weight=1, pad = 2)

		r1 = ['Parameter Name', 'Value']
		# create two columns
		for ci, cLabel in enumerate(r1):
			tk.Grid.columnconfigure(self.f1, ci, weight=1, minsize = 10, pad = 3)
			tk.Label(self.f1, text=cLabel, borderwidth=3, width=10, relief=tk.GROOVE).grid(column=ci, row=0, sticky=N+E+W)

		# create rows
		for i, el in enumerate(self.elementList, 1):
			tk.Label(self.f1, text=el[0], borderwidth=2).grid(column=0, row=i, sticky=E+W)
			self.elDict[el[0]] = tk.StringVar()
			Entry = tk.Entry(self.f1, textvariable=self.elDict[el[0]], justify=tk.CENTER)
			Entry.insert(tk.END, el[1])
			Entry.grid(column=1, row=i, sticky=E+W)
			tk.Grid.rowconfigure(self.f1, i, weight = 1, pad = 2)
			if i == 1:
				Entry.focus_set()
				Entry.select_range(0, tk.END)

		checkButtonA = tk.Checkbutton(self, text = 'Align to Roads', variable = self.alignRoads)
		checkButtonA.grid(row = 6, column = 0, sticky = W)
		if self.outDict['Align to Roads'] == 1:
			checkButtonA.toggle()
		checkButtonR = tk.Checkbutton(self, text = 'Read Offset from Field', variable = self.readField)
		if self.outDict['Read Offset from Field'] == 1:
			checkButtonR.toggle()
		checkButtonR.grid(row = 7, column = 0, sticky = W)

		# self.saveButton = tk.Button(self, text="Save Settings", command=self.both_functions, width=30)
		saveButton = tk.Button(self, text = 'Save Settings', command = self.btnClick, width = 30)
		# self.saveButton.grid(row=4, column=0)
		saveButton.grid(row = 8, column = 0, sticky = E+W)

		top.bind('<Return>', self.btnClick)

	def btnClick(self, event = None):
		# Get values from Entry objects and put into outDict
		for el, newval in self.elDict.items():
			self.outDict[el] = newval.get()
		self.outDict['Align to Roads'] = self.alignRoads.get()
		self.outDict['Read Offset from Field'] = self.readField.get()
		self.top.destroy()


def drawgui(in_els):

	gui = GUI(els = in_els)
	gui.master.title("Enter parameters")
	gui.master.minsize(width = 150, height = 100)
	gui.mainloop()
	return gui.outDict


if __name__ == '__main__':
	a = [float(x) for x in (sys.argv[1]).split(',')]
	# a = [10, 20, 30, 15, 5, 10, 1, 0]
	dic = drawgui([
		['Ortho Threshold', a[0]],
		['Search Radius', a[1]],
		['Rotation Threshold', a[2]],
		['Offset', a[3]],
		['Curves Radius', a[4]],
		['Curves Angle', a[5]],
		['Align to Roads', a[6]],
		['Read Offset from Field', a[7]]
	])

	print dic['Ortho Threshold']
	print dic['Search Radius']
	print dic['Rotation Threshold']
	print dic['Offset']
	print dic['Curves Radius']
	print dic['Curves Angle']
	print dic['Align to Roads']
	print dic['Read Offset from Field']
