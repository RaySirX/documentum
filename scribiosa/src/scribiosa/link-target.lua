function Link(link)
  local extension = FORMAT:match("html") and "html"
    or FORMAT:match("docx") and "docx"
    or FORMAT:match("pdf") and "pdf"

  if not extension then
    return link
  end

  local path, suffix = link.target:match("^([^?#]*)(.*)$")
  local stem, source_extension = path:match("^(.*)(%.[^./]+)$")
  if source_extension and (source_extension:lower() == ".md"
      or source_extension:lower() == ".markdown") then
    link.target = stem .. "." .. extension .. suffix
  end
  return link
end