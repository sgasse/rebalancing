import CSV
import Dates


function _append_combis(in_combis)
    a = []
    for j in 1:size(in_combis, 1)
        push!(a, [in_combis[j] 0])
        push!(a, [in_combis[j] 1])
    end
    return a
end


function combi_to_shares(combi, shares)
    shares = copy(shares)
    for (i, val) in enumerate(combi)
        if val == 1
            shares[i] = ceil(shares[i])
        else
            shares[i] = floor(shares[i])
        end
    end
    return shares
end


function create_share_roundings(shares)
    n = size(shares, 1)
    ti = [0; 1]
    for i=1:(n - 1)
        ti = _append_combis(ti)
    end

    share_roundings = []
    for combi in ti
        cur_shares = combi_to_shares(combi, shares)
        push!(share_roundings, cur_shares)
    end
    return share_roundings
end


function calculate_reinvest_shares(data_file, investment; save=true)
    pf = CSV.read(ARGS[1]; datarow=2, delim=',',
                         types=[String, Float64, Int64, Float64])

    portf_val = sum(pf.price .* pf.shares)

    th_portf_value = portf_val + investment
    th_share_values = pf.goal_ratio * th_portf_value
    th_new_values = th_share_values - pf.price .* pf.shares
    th_new_shares = th_new_values ./ pf.price


    new_share_options = create_share_roundings(th_new_shares)
    best_shares = []
    best_investment = 0.0
    for shares in new_share_options
        cur_investment = sum(pf.price .* shares)
        if cur_investment < investment && cur_investment > best_investment
            best_shares = shares
            best_investment = cur_investment
        end
    end

    rebalanced_values = (pf.shares + best_shares) .* pf.price
    best_shares = convert(Array{Int64,1}, best_shares)
    pf[:reinvest_shares] = best_shares
    pf[:rebalanced_ratio] = rebalanced_values / sum(rebalanced_values)

    if save == true
        timestamp = Dates.format(Dates.now(), "yyyy-mm-dd_HH.MM.SS")
        out_file = "data_rebalanced_" * timestamp * ".csv"
        CSV.write(out_file, pf)
        println("Saved dataframe to ", out_file)
    end
    return pf
end


if size(ARGS)[1] == 2
    data_file = ARGS[1]
    investment = tryparse(Float64, ARGS[2])
    pf = calculate_reinvest_shares(data_file, investment)
    display(pf)
end

