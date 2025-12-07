def parse_results_txt(model):
    with open("results.txt", "r") as file:
        lines = file.readlines()

        for i, line in enumerate(lines):
            lines[i] = line.split(" ")

        model_metrics = []
        for line in lines:
            if f"{model}:" in line:
                metrics = {}
                for element in line:
                    if "=" in element:
                        metric = element.split("=")
                        metrics[metric[0].strip()] = float(metric[1])
                model_metrics.append(metrics)

        return model_metrics

def get_best_model(metrics):
    best_mae = metrics[0]["mae"]
    best_model_index = 0
    for i in range(1, len(metrics)):
        if metrics[i]["mae"] < best_mae:
            best_mae = metrics[i]["mae"]
            best_model_index = i

    return best_model_index, metrics[best_model_index]


BEST_LSTM_MODEL = get_best_model(parse_results_txt("lstm"))[0]
BEST_BLSTM_MODEL = get_best_model(parse_results_txt("blstm"))[0]


if __name__ == "__main__":
    lstm = parse_results_txt("lstm")
    blstm = parse_results_txt("blstm")
    transformer = parse_results_txt("transformer")

    best_lstm_index, best_lstm = get_best_model(lstm)
    best_blstm_index, best_blstm = get_best_model(blstm)
    best_transformer_index, best_transformer = get_best_model(transformer)

    print(best_lstm_index, best_lstm)
    print(best_blstm_index, best_blstm)
    print(best_transformer_index, best_transformer)
