import argparse
from ROOT import gROOT, TCanvas, TLegend, TGraph, TDatime, TH2F, gStyle, kRed, kBlue, kBlack, kMagenta, TFile
from datetime import datetime
gStyle.SetOptStat(0)

#from matplotlib import pyplot as plt

# get database measurements first: python TMB_AG.py - store in text files TMB_0V.txt and TMB_HV0.txt
# Dose information from: http://pnpi-cms-l1.cern.ch:8080/CSCdose/ - stored in chargevtime.txt
# can process that nasty text file to slightly more readable form with getcharges.py
# for now 16 seems like a good choice of clct
parser = argparse.ArgumentParser(description='plot TMB Dump results over time for a chosen CLCT. Input text files generated by dumping output of TMB_AG.py to text file. Before running this be sure to manually check input for errors in database or measurement outliers & remove/correct them accordingly. \n Please also ensure that each HV0 measurement has exactly one corresponding 0V measurement and vice versa.\n As of writing the goal is to look at measurements from Sept 2017 onwards.')
parser.add_argument('--clctnum', action='store', default=16, type=int, help=" Available numbers are 14-20 \n DEFAULT: 16")
parser.add_argument('--startdate', action='store', default="01 SEP 2015", type=str, help="Starting date: write as DD MTH YYYY where MTH is the 3 letter abbreviation for the month\n DEFAULT: 01 SEP 2017")
parser.add_argument('--timeplot', action='store_true', default=False, help="Plot with time as the x axis as opposed to charge\n DEFAULT: False")
parser.add_argument('--tenpctzero', action='store_true', help=" Plotting over the entire region of charge accumulation or just for 2 percent CF4\n DEFAULT: False")
parser.add_argument('--validatewithold', action='store_true', help=" For validating with Long Wang's Old Results\n DEFAULT: False")
parser.add_argument('--plotproblem', action='store_true', help=" Plot problem WG 5 in layer 5 me11 vs normal WG 4\n DEFAULT: False")
parser.add_argument('--plotcathodes', action='store_true', help="Show CFEB and CLCT plots or no\n DEFAULT: False")
parser.add_argument('--plotname', action='store', type=str, default='Sept17-Jun21', help="Name of output plots\n DEFAULT: Sept17-Jun21")
parser.add_argument('--test11compare', action='store_true', help="for comparing test 11 ALCT rates with TMB dump ALCT rates (By default this macro still uses test 11 to correct for noisy wg in layer 5 regardless of this value)\n DEFAULT: False")
parser.add_argument('--charges', action ='store', default='charges_me11_2pct.txt', type=str, help="list of charges - 'outfile' from getcharges.py\n DEFAULT: charges_me11_2pct.txt")
parser.add_argument('--DatHV0', action ='store', default='TMB_HV0_me11_2pct.txt', type=str, help="of HV0 TMB Dump measurements\n DEFAULT: TMB_HV0_me11_2pct.txt")
parser.add_argument('--Dat0V', action ='store', default='TMB_0V_me11_2pct.txt', type=str, help="list of 0V TMB Dump measurements\n DEFAULT: TMB_0V_me11_2pct.txt")
parser.add_argument('--DatT11', action ='store', default='anode_me11_2pct.txt', type=str, help="list of Test 11 measurements\n DEFAULT: anode_me11_2pct.txt")

args = parser.parse_args()
class Legend:
    def __init__(self, xmin=0.1, ymin=0.7, xmax=0.3, ymax=0.9):
        self.legend = TLegend(xmin, ymin, xmax, ymax)
        self.legend.SetHeader("Legend", "C")
    def fill(self, tgraphs):
        for tgraph in tgraphs:
            self.legend.AddEntry(tgraph.graph, tgraph.title, "lp")
    def draw(self):
        self.legend.Draw()
class Graph:
    def __init__(self, length, name, color, cathodeOrTMB = False, correction=False):
        self.graph = TGraph(length)
        self.title = name
        self.color = color
        self.iscorrection = correction
        self.iscathodeortmb = correction
    def fill(self, i, xpoint, ypoint):
        self.graph.SetPoint(i, xpoint, ypoint)
    def draw(self):
        self.graph.SetMarkerColor(self.color)
        self.graph.SetMarkerSize(2)
        if self.iscorrection:
            self.graph.SetLineColor(kBlack)
            self.graph.SetMarkerStyle(24)
        elif self.iscathodeortmb:
            self.graph.SetLineColor(self.color)
            self.graph.SetMarkerStyle(21)
        else:
            self.graph.SetLineColor(self.color)
            self.graph.SetMarkerStyle(20)
        self.graph.Draw("PL SAME")
class Limits:
    def __init__(self, innername, title, xtitle, ytitle, xbins, xmin, xmax, ybins, ymin, ymax):
        self.lims = TH2F(innername, title+";"+ xtitle + ";" + ytitle, xbins, xmin, xmax, ybins, ymin, ymax)
        self.lims.Draw()
        self.lims.GetXaxis().SetLabelSize(0.03)
        self.lims.GetYaxis().SetLabelSize(0.03)
        self.lims.GetYaxis().SetTitleSize(0.08)
        self.lims.GetYaxis().SetTitleOffset(0.5)
        if args.timeplot:
            self.lims.GetXaxis().SetTimeDisplay(1)
            self.lims.GetXaxis().SetTimeOffset(0)
            self.lims.GetXaxis().SetTimeFormat("%d.%b.%Y")
            #self.lims.GetXaxis().SetNdivisions(507)
            #self.lims.GetXaxis().SetTimeOffset(24, "gmt")

starttime = datetime.strptime(args.startdate, "%d %b %Y")
tmbdump_0v = []
tmbdump_hv0 = []
CLCT_NUM = args.clctnum - 5
numlines_0v = sum(1 for line in open(args.Dat0V))
numlines_hv0 = sum(1 for line in open(args.DatHV0))

if numlines_0v != numlines_hv0:
    print "ERROR: Number of lines in the two input files is not the same - make sure you have consistent matchup between the dates of each measurement being used"
    print "0V: ", numlines_0v
    print "HV0: ", numlines_hv0
    quit()

def GetTotalCorrectedRate(rootfilename):
    summedhits = 0
    corrections = 0
    rootfile = TFile(rootfilename, "read")
    for layernum in xrange(0,6):
        hname = str("ALCT/hNofAhitL["+str(layernum)+"][2]")
        hist = rootfile.Get(hname)
        if hist != 0:
            entries = hist.GetEntries()
            summedhits += entries
    hist2 = rootfile.Get("ALCT/hNofAhit[2]")
    for binnum in xrange(2, 8):
        NumOfLayers = binnum - 2
        NHits = hist2.GetBinContent(binnum)
        LayerCorrection = 0
        if NumOfLayers != 0:
            LayerCorrection = NHits * (NumOfLayers - 1) / NumOfLayers
        corrections += LayerCorrection
    CorrectedTotalRate = (summedhits - corrections) / 30
    rootfile.Close()
    return CorrectedTotalRate
with open(args.Dat0V, "r") as f0:
    for linenum, line in enumerate(f0):
        #skip preamble
        if linenum <= 5:
            continue
        #debug statement
        #if linenum == 15:
        #    break
        line_arr = []
        for index, item in enumerate(line.split()):
            #skip database number, comma and UTC time of measurement [included with date as single string], srcdwn, L1A, and comment
            #output vector will have [datime, HV, t[sec], 0ALCT, 13CLCT (aka the CFEB, which should sum all the values from the CLCTs), Input CLCT number, TMB]
            if index == 0 or index == 2 or index == 3 or index == 5 or index >= 17:
                continue
            #take only the chosen cfeb
            if index != CLCT_NUM and index > 8 and index <= 15:
                continue
            if index == 1:
                #keep date as a string
                datime = str(item + line.split()[2] + ' ' + line.split()[3])
                line_arr += [datime]
            elif index == 4:
                #Keep voltage setup as a string
                line_arr += [str(item)]
            else: 
                line_arr += [float(item)]
        tmbdump_0v += [line_arr]
    f0.close()

#titleline= open(args.DatHV0, "r").readlines()[5]
#print titleline
with open(args.DatHV0, "r") as f1:
    for linenum, line in enumerate(f1):
        #skip preamble
        if linenum <= 5:
            continue
        #if linenum == 20 or linenum == 21 or linenum == 22:
        #    print line
        #if linenum == 15:
        #    break
        line_arr = []
        for index, item in enumerate(line.split()):
            #skip database number, comma and UTC time of measurement [included with date as single string], srcdwn, L1A, and comment
            #output vector will have [datime, HV, t[sec], 0ALCT, 13CLCT (aka the CFEB, which should sum all the values from the CLCTs), Chosen CLCT, TMB]
            if index == 0 or index == 2 or index == 3 or index == 5 or index >= 17:
                continue
            #take only the chosen cfeb
            if index != CLCT_NUM and index > 8 and index <= 15:
                continue
            if index == 1:
                #keep date as a string
                datime = str(item + line.split()[2] + ' ' + line.split()[3])
                line_arr += [datime]
            elif index == 4:
                #Keep voltage setup as a string
                line_arr += [str(item)]
            else: 
                #if (linenum == 20 or linenum == 21 or linenum == 22) and (index == 16 or index == 9 or index == 10):
                #    print titleline.split()[index-1]
                #    print item
                line_arr += [float(item)]
        tmbdump_hv0 += [line_arr]
    f1.close()

qtot = []
# importing charge data for me11 - check with time consistency already done by getcharges.py
with open(args.charges, "r") as f2:
    for linenum, line in enumerate(f2):
        if args.tenpctzero:
            qtot += [float(line)+330]
        else:
            qtot += [float(line)]
    f2.close()
if len(qtot) != len(tmbdump_0v):
    print "ERROR: mismatch in number of charge measurements and number of TMB dump measurements"
    print "TMB: ", len(tmbdump_0v)
    print "Charge: ", len(qtot)
    quit()
#Loading info for Test 11 ALCT rates

if args.test11compare:
    t11fullCorralctrates = []
rootfiles = []
with open(args.DatT11, "r") as f1:
    for lnum, line in enumerate(f1):
        if lnum == 0: continue
        rootfiles += [str(line.split()[0])]
        if args.test11compare:
            t11fullCorralctrates += [GetTotalCorrectedRate(rootfiles[-1])]
    f1.close()
if len(rootfiles) != len(tmbdump_0v):
    print "ERROR: Mismatch in number of Test 11 results and number of TMB dump measurements"
    print "TMB: ", len(tmbdump_0v)
    print "Test 11: ", len(rootfiles)
    quit()

#produce final arrays for plotting
#plotALCTrates_Q = TGraph(len(tmbdump_hv0))
if args.test11compare:
    plotALCTrates = Graph(len(tmbdump_hv0), "TMB Dump ALCT0 Rate", kRed+3)
    plotTest11_TotalHitClusterRates = Graph(len(tmbdump_hv0), "Total Anode Hit Cluster Rate", kBlue)
    plotTest11_TotalHitCluster_MinusMuonRates = Graph(len(tmbdump_hv0), "Single Layer Anode Hit Cluster Rate", kBlue+3)
    #plotTest11_TotalHitClusterRates_Q = TGraph(len(tmbdump_hv0))
    #plotTest11_TotalHitCluster_MinusMuonRates_Q = TGraph(len(tmbdump_hv0))
else:
    plotALCTrates = Graph(len(tmbdump_hv0), "ALCT", kRed+3)
    plotCorrALCTrates = Graph(len(tmbdump_hv0), "ALCT Corrected", kRed+3, False, True)
    plotTMBrates = Graph(len(tmbdump_hv0), "TMB (ALCT*CLCT)", kBlue+3, True)
    if args.plotproblem:
        plotProblemWGrates = Graph(len(tmbdump_hv0), "Problem WG 5 Layer 5", kRed+3)
        plotNormalWGrates = Graph(len(tmbdump_hv0), "Normal WG 4 Layer 5", kBlue+3)
        #plotProblemWGrates_Q = TGraph(len(tmbdump_hv0))
        #plotNormalWGrates_Q = TGraph(len(tmbdump_hv0))
    if args.plotcathodes:
        plotCFEBrates = Graph(len(tmbdump_hv0), "CFEB", kMagenta+2, True)
        plotCLCTrates = Graph(len(tmbdump_hv0), "CLCT#"+str(args.clctnum), kBlue, True)
        #plotCFEBrates_Q = TGraph(len(tmbdump_hv0))
        #plotCLCTrates_Q = TGraph(len(tmbdump_hv0))
    #plotCorrALCTrates_Q = TGraph(len(tmbdump_hv0))
    #plotTMBrates_Q = TGraph(len(tmbdump_hv0))
rmax = 0
rmin = 1000000000000
qmax = 500
j=0
tdtmin = datetime.strptime(tmbdump_0v[0][0], "%d-%b-%Y, %H:%M:%S") 
tdtmax = datetime.strptime(tmbdump_0v[len(tmbdump_hv0)-1][0], "%d-%b-%Y, %H:%M:%S") 

for i in xrange(len(tmbdump_hv0)):
    pydt = datetime.strptime(tmbdump_hv0[i][0], "%d-%b-%Y, %H:%M:%S") 
    pydt_ = datetime.strptime(tmbdump_0v[i][0], "%d-%b-%Y, %H:%M:%S") 
    if (abs(pydt_-pydt).seconds/3600 > 24):
        print "Too large time difference between 0v and HV0 measurements at", tmbdump_hv0[i][0]
        quit()
    if pydt_ < starttime:
        continue
    thv0 = float(tmbdump_hv0[i][2])
    t0v = float(tmbdump_0v[i][2])
    if thv0 == 0 or t0v == 0:
        print "Time error for measurement at: ", tmbdump_0v[i][0]
        quit()
    alct = tmbdump_hv0[i][3]/thv0 - tmbdump_0v[i][3]/t0v
    t11file = TFile(rootfiles[i], "read")
    if args.test11compare:
        t11alct = t11fullCorralctrates[i]
        t11alct0 = t11file.Get("ALCT/hNofAhit[2]").GetBinContent(3)/30.0
    else:
        t11hist = t11file.Get("ALCT/hAhitL[4][1]")
        #The bad WG is 5, but histogram bins start counting from 1 (the first bin would be at zero) and in addition the WG start counting at 1 - with bin 1 left empty, so 2 is added to the desired wg to get the index.
        l5bad = t11hist.GetBinContent(7)/30
        l5good = t11hist.GetBinContent(8)/30
        corralct = alct - l5bad + l5good
        print("alct: "+str(alct)+" l5bad: "+str(l5bad)+" l5good: "+str(l5good))
        if args.plotcathodes:
            cfeb = tmbdump_hv0[i][4]/thv0 - tmbdump_0v[i][4]/t0v
            clct = tmbdump_hv0[i][5]/thv0 - tmbdump_0v[i][5]/t0v
    tmb = tmbdump_hv0[i][6]/thv0 - tmbdump_0v[i][6]/t0v
    dt = TDatime(pydt.year, pydt.month, pydt.day, pydt.hour, pydt.minute, pydt.second)
    t = dt.Convert()
    if args.tenpctzero:
        if qtot[i] > qmax:
            qmax = qtot[i]
    if args.timeplot:
        yvar = t
    else:
        yvar = qtot[i]
    plotALCTrates.fill(i, yvar, alct/1000.0) 
    if args.test11compare:
        plotTest11_TotalHitClusterRates.fill(i, yvar, t11alct/1000.0) 
        plotTest11_TotalHitCluster_MinusMuonRates.fill(i, yvar, t11alct0/1000.0) 
    else:
        plotCorrALCTrates.fill(i, yvar, corralct/1000.0) 
        plotTMBrates.fill(i, yvar, tmb/1000.0) 
        if args.plotproblem:
            plotProblemWGrates.fill(i, yvar, l5bad) 
            plotNormalWGrates.fill(i, yvar, l5good) 
        if args.plotcathodes:
            plotCFEBrates.fill(i, yvar, cfeb/1000.0) 
            plotCLCTrates.fill(i, yvar, clct/1000.0) 
        #    break

    if alct > rmax:
        rmax = alct
    if args.plotcathodes:
        if cfeb > rmax:
            rmax = cfeb
        if clct > rmax:
            rmax = clct
    if tmb > rmax:
        rmax = tmb

    if alct < rmin:
        rmin = alct
    if args.plotcathodes:
        if cfeb < rmin:
            rmin = cfeb
        if clct < rmin:
            rmin = clct
    if tmb < rmin:
        rmin = tmb
    #if args.plotcathodes:
    #        print datetime.strftime(pydt, "%d-%b-%Y"), "ALCT ", alct, " CFEB ", cfeb, " CLCT ", clct, " TMB ", tmb, "Charge (mC/cm): ", qtot[i]
    #else:
    #    print datetime.strftime(pydt, "%d-%b-%Y"), "ALCT ", alct, " TMB ", tmb, "Charge (mC/cm): ", qtot[i]
    
print tdtmin, tdtmax
tmin = TDatime(tdtmin.year, tdtmin.month, tdtmin.day, tdtmin.hour, tdtmin.minute, tdtmin.second).Convert()
tmax = TDatime(tdtmax.year, tdtmax.month, tdtmax.day, tdtmax.hour, tdtmax.minute, tdtmax.second).Convert()
print TDatime(tmin).GetDay(), TDatime(tmin).GetMonth(), TDatime(tmin).GetYear() 
print TDatime(tmax).GetDay(), TDatime(tmax).GetMonth(), TDatime(tmax).GetYear() 


#Plotting 

fivedays = 432000
if args.timeplot:
    namesuffix = "_Time"
else:
    namesuffix = "_Charge"
if args.test11compare:
    Test11CompareCanvas = TCanvas("Test11CompareCanvas", "Anode Dark Rate Comparison", 200, 10, 1400, 1000)
    Test11CompareCanvas.cd()
    if args.timeplot:
        Test11CompareLims = Limits("t11comparelimits", "ALCT Rates Test 11 vs TMB dumps", "Date of Measurement", "Dark Rate (kHz)", 1000, tmin-fivedays, tmax+fivedays, 100, 0, 2)
    else:
        Test11CompareLims = Limits("t11comparelimits", "ALCT Rates Test 11 vs TMB dumps", "Accumulated Charge (mC/cm)", "Dark Rate (kHz)", 1000, 330, qmax + 10, 100, 0, 2)
    plotALCTrates.draw()
    plotTest11_TotalHitClusterRates.draw()
    plotTest11_TotalHitCluster_MinusMuonRates.draw()
    Test11CompareLegend = Legend(0.1, 0.7, 0.6, 0.9)
    Test11CompareLegend.fill([plotALCTrates, plotTest11_TotalHitClusterRates, plotTest11_TotalHitCluster_MinusMuonRates])
    Test11CompareLegend.draw()
    Test11CompareCanvas.SaveAs("DarkRates_" + args.plotname + "_AnodeCompare" + namesuffix + ".pdf")
elif args.plotproblem:
    ProblemCanvas = TCanvas("ProblemCanvas", "Problem and Normal WG Dark Rate vs Time", 200, 10, 1400, 1000)
    ProblemCanvas.SetLogy()
    ProblemCanvas.cd()
    if args.timeplot:
        ProblemLimits = Limits("problemlimits", "Problem WG vs Normal", "Date of Measurement", "Dark Rate (Hz)", 1000, tmin-fivedays, tmax+fivedays, 100, 10**(-1), 10**4)
    else:
        ProblemLimits = Limits("problemlimits", "Problem WG vs Normal", "Accumulated Charge (mC/cm)", "Dark Rate (Hz)", 1000, 330, 750, 100, 10**(-1), 10**4)
    plotProblemWGrates.draw()
    plotNormalWGrates.draw()
    ProblemLegend = Legend()
    ProblemLegend.fill([plotProblemWGrates, plotNormalWGrates])
    ProblemLegend.draw()
    ProblemCanvas.SaveAs("DarkRates_" + args.plotname + "_ProblemVSNormalWG" + namesuffix + ".pdf")
else:
    TMBRateCanvas = TCanvas("TMBRateCanvas", "Dark rate vs Time", 200, 10, 1400, 1000)
    TMBRateCanvas.cd()
    if args.timeplot:
        TMBRateLimits = Limits("TMBRatelimits", "Dark Rates", "Date of Measurement", "Dark Rate (kHz)", 1000, tmin-fivedays, tmax+fivedays, 100, 0, 10)
    elif args.validatewithold:
        TMBRateLimits = Limits("TMBRatelimits", "TMB Dump Dark Rates", "Accumulated Charge (mC/cm)", "Dark Rate (kHz)", 1000, 0, 500, 100, 0, 5)
    else:
        print(qmax)
        TMBRateLimits = Limits("TMBRatelimits", "TMB Dump Dark Rates", "Accumulated Charge (mC/cm)", "Dark Rate (kHz)", 1000, qtot[0], qmax + 10, 100, 0, 8)
    plotALCTrates.draw()
    plotCorrALCTrates.draw()
    plotTMBrates.draw()
    #A chambertype parameter is necessary
    #toplot = [plotALCTrates, plotCorrALCTrates, plotTMBrates]
    toplot = [plotALCTrates, plotTMBrates]
    if args.plotcathodes:
        plotCFEBrates.draw()
        plotCLCTrates.draw()
        toplot += [plotCFEBrates, plotCLCTrates]
    TMBDumpLegend = Legend()
    TMBDumpLegend.fill(toplot)
    TMBDumpLegend.draw()
    TMBRateCanvas.SaveAs("DarkRates_" + args.plotname + namesuffix + ".pdf")
