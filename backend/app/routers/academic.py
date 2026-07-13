"""学术搜索路由 — AMiner + OpenAlex 统一接口"""

from fastapi import APIRouter, Depends, Query
from ..auth import get_current_user
from ..services.academic_search import (
    aminer_search_scholar, aminer_search_paper, aminer_paper_detail, aminer_qa_search,
    openalex_search_works, openalex_search_authors,
)

router = APIRouter(prefix="/api/academic", tags=["学术搜索"])


# ======== AMiner ========

@router.get("/aminer/scholar")
async def search_aminer_scholar(name: str = Query(default=""), org: str = Query(default=""), size: int = 10, current_user=Depends(get_current_user)):
    return await aminer_search_scholar(name=name, org=org, size=size)


@router.get("/aminer/paper")
async def search_aminer_paper(title: str = Query(default=""), keyword: str = Query(default=""), author: str = Query(default=""), page: int = 0, size: int = 10, current_user=Depends(get_current_user)):
    return await aminer_search_paper(title=title, keyword=keyword, author=author, page=page, size=size)


@router.get("/aminer/paper/{paper_id}")
async def get_aminer_paper_detail(paper_id: str, current_user=Depends(get_current_user)):
    return await aminer_paper_detail(paper_id)


@router.get("/aminer/qa")
async def aminer_qa(query: str, size: int = 10, current_user=Depends(get_current_user)):
    return await aminer_qa_search(query=query, size=size)


# ======== OpenAlex ========

@router.get("/openalex/works")
async def search_openalex_works(query: str = Query(default=""), page: int = 1, year_from: str = Query(default=""), year_to: str = Query(default=""), oa_only: bool = False, current_user=Depends(get_current_user)):
    filters = []
    if year_from: filters.append(f"from_publication_date:{year_from}-01-01")
    if year_to: filters.append(f"to_publication_date:{year_to}-12-31")
    if oa_only: filters.append("is_oa:true")
    filter_str = ",".join(filters) if filters else ""
    return await openalex_search_works(query=query, filter_str=filter_str, page=page)


@router.get("/openalex/authors")
async def search_openalex_authors(query: str, page: int = 1, current_user=Depends(get_current_user)):
    return await openalex_search_authors(query=query, page=page)
