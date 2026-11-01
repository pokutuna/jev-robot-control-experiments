-- 「図 N: ...」で始まる段落を図のキャプションとして caption クラスの div で囲む
function Para(el)
  local c = el.content
  if #c >= 3 and c[1].t == "Str" and c[1].text == "図"
      and c[2].t == "Space"
      and c[3].t == "Str" and c[3].text:match("^%d+:$") then
    return pandoc.Div({ el }, pandoc.Attr("", { "caption" }))
  end
end
