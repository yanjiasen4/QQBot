import wap

server = 'http://api.wolframalpha.com/v1/query.jsp'
appid = 'HPUTPL-P3E7LY9UG5'

class WolframAlphaResult:
    
    def __init__(self, input):
        self.waeo = wap.WolframAlphaEngine(appid, server)
        self.inpt = input

    def calcResult(self):
        query = self.waeo.CreateQuery(self.inpt)
        raw_result = self.waeo.PerformQuery(query)
        content = wap.WolframAlphaQueryResult(raw_result)
        result = None
        resultImg = None
        if content.IsSuccess():
            dataType = content.DataTypes()[0]
            if dataType == 'Math':
                for pod in content.Pods():
                    waPod = wap.Pod(pod)
                    print waPod.Title()[0]
                    pTitle = str(waPod.Title()[0])
                    if pTitle == 'Result' or 'result' in pTitle: 
                        waSubpod = wap.Subpod(waPod.Subpods()[0])
                        result = waSubpod.Plaintext()[0]
            elif 'MathematicalFunctionIdentity' in dataType:
                for pod in content.Pods():
                    waPod = wap.Pod(pod)
                    if str(waPod.Title()[0]) == 'Decimal approximation':
                        waSubpod = wap.Subpod(waPod.Subpods()[0])
                        result = waSubpod.Plaintext()[0]
            else:
                for pod in content.Pods():
                    waPod = wap.Pod(pod)
                    solvedResults = ['Differential equation solution', 'Limit']
                    waPodTitle = str(waPod.Title()[0])
                    if 'integral' in waPodTitle or waPodTitle in solvedResults:
                        waSubpod = wap.Subpod(waPod.Subpods()[0])
                        result = waSubpod.Plaintext()[0]
                        rightIndex = result.rindex('=') + 2
                        result = result[rightIndex:]
                        img = waSubpod.Img()
                        resultImg = wap.scanbranches(img[0], 'src')[0]
                        break
                    elif 'Result' in waPodTitle:
                        waSubpod = wap.Subpod(waPod.Subpods()[0])
                        result = waSubpod.Plaintext()[0]
                        img = waSubpod.Img()
                        resultImg = wap.scanbranches(img[0], 'src')[0]
                    else:
                        continue
        return result, resultImg

